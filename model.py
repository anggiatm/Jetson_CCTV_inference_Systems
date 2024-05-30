#
# Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

from jetson_inference import imageNet, detectNet, segNet, poseNet, actionNet, backgroundNet
from jetson_utils import cudaFont, cudaDrawRect, cudaDrawLine, Log, cudaDrawCircle
class Model:
    """
    Represents DNN models for classification, detection, pose, ect.
    """
    def __init__(self, model, labels='', colors='', input_layer='', output_layer='', detection_threshold = 0.5, **kwargs):
        """
        Load the model, either from a built-in pre-trained model or from a user-provided model.
        
        Parameters:
        
            type (string) -- the type of the model (classification, detection, ect)
            model (string) -- either a path to the model or name of the built-in model
            labels (string) -- path to the model's labels.txt file (optional)
            input_layer (string or dict) -- the model's input layer(s)
            output_layer (string or dict) -- the model's output layers()
        """
        self.results = None
        self.font = cudaFont()

        self.input_area_color = (10, 10, 160, 80)
        self.line_color = (255,0,200,200)
        self.dot_color = (255, 0, 0, 200)
        self.object_color = (5, 200, 5, 70)
        self.classes_text_color = (5, 200, 5, 200)

        self.net = detectNet(model=model, labels=labels, colors=colors,
                                 input_blob=input_layer, 
                                 output_cvg='scores',
                                 output_bbox='boxes',
                                 threshold = detection_threshold)
            
    def Process(self, img):
        self.results = self.net.Detect(img, overlay='none')
        return self.results

    def overlayCentroid(self, img, centroid, bbox, obj_id, classes, score):
        cudaDrawCircle(img, (centroid[0], centroid[1]), 6, self.dot_color)
        cudaDrawRect(img, bbox, self.object_color)
        text = str(obj_id) +" | "+ str(classes)+ " | " + str(round(score * 100)) + "%"
        self.font.OverlayText(img, img.width, img.height, text, centroid[0] + 15, centroid[1], self.classes_text_color, (0, 0, 0, 0))
        return img

    def overlayFPS(self, img):
        self.font.OverlayText(img, img.width, img.height, "{:.0f} FPS".format(self.net.GetNetworkFPS()), 10, 10, (0,255,0,255), (0, 0, 0, 0))
        return img

    def overlayROI(self, img, detect_roi, input_area):
        cudaDrawRect(img, input_area, self.input_area_color)
        cudaDrawLine(img, (detect_roi[0], detect_roi[1]), (detect_roi[2], detect_roi[1]), self.line_color, 2)
        cudaDrawLine(img, (detect_roi[0], detect_roi[3]), (detect_roi[2], detect_roi[3]), self.line_color, 2)
        cudaDrawLine(img, (detect_roi[0], detect_roi[1]), (detect_roi[0], detect_roi[3]), self.line_color, 2)
        cudaDrawLine(img, (detect_roi[2], detect_roi[1]), (detect_roi[2], detect_roi[3]), self.line_color, 2)
        return img
        
    @staticmethod
    def Usage():
        """
        Return help text for when the app is started with -h or --help
        """
        return imageNet.Usage() + detectNet.Usage() + segNet.Usage() + actionNet.Usage() + poseNet.Usage() + backgroundNet.Usage() 
