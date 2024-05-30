#!/usr/bin/env python3
#
# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the 'Software'),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
import os
import threading
import traceback
import random

import numpy as np
from PIL import Image
from io import BytesIO

from model import Model
from jetson_utils import videoSource, videoOutput, cudaCrop, cudaAllocMapped, cudaToNumpy, cudaResize, saveImageRGBA

from centroidtracker import CentroidTracker
import datetime
import time
from classification import Classification

# import queue

class Stream(threading.Thread):
    """
    Thread for streaming video and applying DNN inference
    """
    def __init__(self, args):
        super().__init__()

        self.model = Model(
            model=args['detection'],
            labels=args['labels'],
            input_layer=args['input_layer'],
            output_layer=args['output_layer'],
            detection_threshold = args['detection_threshold'])

        self.gender = Classification(model='/home/jetson/app/model/classification/gender.onnx', labels='/home/jetson/app/model/classification/gender.txt', input_layer='input_0', output_layer='output_0')
        self.age_male = Classification(model='/home/jetson/app/model/classification/age_male.onnx', labels='/home/jetson/app/model/classification/age_male.txt', input_layer='input_0', output_layer='output_0')
        self.age_female = Classification(model='/home/jetson/app/model/classification/age_female.onnx', labels='/home/jetson/app/model/classification/age_female.txt', input_layer='input_0', output_layer='output_0')

        self.input = videoSource(args['input'], options={'numBuffers':5, 'loop':-1})
        self.detect_roi = args['detect_roi']
        self.input_area =  args['input_area']
        self.format = 'rgb8'
        self.saved_detection_path = args['saved_detection_path']
        self.centroid_tracker = CentroidTracker()
        self.area1 = []
        self.img = cudaAllocMapped(width=1280, height=720, format=self.format)
        self.detect_buffer = args['detect_buffer']
        self.last_image_deque = args['last_image_deque']

    def process(self):
        img = self.input.Capture(format=self.format, timeout=2000)
        imgOutput = cudaAllocMapped(width = self.getCropDimension()[0], height=self.getCropDimension()[1], format=self.format)
        cudaCrop(img, imgOutput, self.detect_roi)

        if img is None:  # timeout
            return

        results = self.model.Process(imgOutput)
        del imgOutput

        rects, class_ids, scores = self.calculateROI(results)
        tracked_objects, tracked_classes, tracked_rects, tracked_scores = self.centroid_tracker.update(rects, class_ids, scores)

        for obj_id, centroid in tracked_objects.items():
            
            if self.isInsideArea(self.input_area, centroid) and obj_id not in self.area1:
                if len(self.area1) > 30:
                    self.area1.pop(0)
                self.area1.append(obj_id)
            elif not self.isInsideArea(self.input_area, centroid) and obj_id in self.area1:
                bbox = tracked_rects[obj_id]
                classes = tracked_classes[obj_id]
                score = tracked_scores[obj_id]

                self.area1.remove(obj_id)
                self.handleNewItem(img, classes, score, bbox)
            # img = self.model.overlayCentroid(img, centroid, bbox, obj_id, classes, score)

        # OVERLAY
        for obj_id, centroid in tracked_objects.items():
            bbox = tracked_rects[obj_id]
            classes = tracked_classes[obj_id]
            score = tracked_scores[obj_id]
            img = self.model.overlayCentroid(img, centroid, bbox, obj_id, classes, score)

        img = self.model.overlayFPS(img)
        img = self.model.overlayROI(img, self.detect_roi, self.input_area)
        cudaResize(img, self.img)

    def calculateROI(self, results):
        objects = []
        for result in results:
            class_id = result.ClassID
            class_name = self.model.net.GetClassDesc(class_id)
            confidence = result.Confidence
            xmin, ymin, xmax, ymax = result.ROI
            xmin = self.detect_roi[0] + int(max(1, xmin))
            xmax = self.detect_roi[0] + int(min(self.detect_roi[2] - self.detect_roi[0], xmax))
            ymin = self.detect_roi[1] + int(max(1, ymin))
            ymax = self.detect_roi[1] + int(min(self.detect_roi[3] - self.detect_roi[1], ymax))
            bounding_box = (xmin, ymin, xmax, ymax)
            objects.append({
                "id": class_id,
                "class": class_name,
                "confidence": confidence,
                "bbox": bounding_box
            })
        # Gunakan Centroid Tracker di sini
        rects = [obj['bbox'] for obj in objects]
        class_ids = [obj['id'] for obj in objects]
        scores = [obj['confidence'] for obj in objects]

        return rects, class_ids, scores
    
    def generate_frames(self):
        while True:
            time.sleep(0.4)
            frame_pil = Image.fromarray(cudaToNumpy(self.img))

            with BytesIO() as output:
                frame_pil.save(output, format='JPEG', quality=70)
                jpeg_bytes = output.getvalue()

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n\r\n"
            )

    def getDetectBuffer(self):
        result_array = []
        while not self.detect_buffer.empty():
            result_array.append(self.detect_buffer.get())
        return result_array
    
    def addDetectBuffer(self, item):
        self.detect_buffer.put(item)

    def handleNewItem(self, img, classes, score, bbox):
        current_time = datetime.datetime.now()
        random_number = random.randint(10000, 99999)

        crop_image = cudaAllocMapped(width=bbox[2] - bbox[0], height=bbox[3] - bbox[1], format=img.format)
        cudaCrop(img, crop_image, bbox)

        gender_id, gender_score = self.gender.Process(crop_image)

        age = []
        img_name = ""
        if gender_id == 0:
            age = self.age_male.Process(crop_image)
            img_name = f"{self.saved_detection_path}{current_time.strftime('%d%m%y')}/male/{age[0]}/{current_time.strftime('%d%m%y-%H%M%S')}_{random_number}.jpg"
        else:
            age = self.age_female.Process(crop_image)
            img_name = f"{self.saved_detection_path}{current_time.strftime('%d%m%y')}/female/{age[0]}/{current_time.strftime('%d%m%y-%H%M%S')}_{random_number}.jpg"

        bufferItem = {
            'gender' : gender_id, 
            'gender_score' : round(gender_score * 100), 
            'age' : age[0], 
            'age_score' : round(age[1] * 100),
            'attr_headwear' : 0, 
            'attr_mask' : 0, 
            'attr_glasses' : 0, 
            'image_path' : img_name, 
            'timestamp' : current_time, 
        }

        self.addDetectBuffer(bufferItem)
        self.last_image_deque.append(bufferItem)
        
        folder_path = f"{self.saved_detection_path}{current_time.strftime('%d%m%y')}"

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            os.makedirs(folder_path+'/male')
            os.makedirs(folder_path+'/female')
            os.makedirs(folder_path+'/male/0')
            os.makedirs(folder_path+'/male/1')
            os.makedirs(folder_path+'/male/2')
            os.makedirs(folder_path+'/male/3')

            os.makedirs(folder_path+'/female/0')
            os.makedirs(folder_path+'/female/1')
            os.makedirs(folder_path+'/female/2')
            os.makedirs(folder_path+'/female/3')

        saveImageRGBA(img_name, crop_image, bbox[2] - bbox[0], bbox[3] - bbox[1])
        del crop_image

    def getCropDimension(self):
        width = self.detect_roi[2] - self.detect_roi[0]
        height = self.detect_roi[3] - self.detect_roi[1]
        return [width, height]

    def isInsideArea(self, rectangle, point):
        left, top, right, bottom = rectangle
        x, y = point
        # Cek apakah x berada di antara left dan right, dan y berada di antara top dan bottom
        return left <= x <= right and top <= y <= bottom

    def run(self):
        while True:
            try:
                self.process()
            except:
                traceback.print_exc()

    @staticmethod
    def usage():
        return videoSource.Usage() + videoOutput.Usage() + Model.Usage()
        
