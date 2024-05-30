#!/usr/bin/env python3

import os
import threading
import flask
import base64
import queue
from stream import Stream
from datetime import datetime

from db import DB
from config import Config

import time
import atexit
import psutil
from apscheduler.schedulers.background import BackgroundScheduler
from collections import deque
from device import DeviceInfo

last_image_deque = deque(maxlen=8)

database = DB(Config.DB_HOST, Config.DB_USER, Config.DB_PASS, Config.DB_NAME)
database_central = DB(Config.DB_CENTRAL_HOST, Config.DB_CENTRAL_USER, Config.DB_CENTRAL_PASS, Config.DB_CENTRAL_NAME)

detect_buffer = queue.Queue()

config_default = database.get_config(Config.LOBBY_NAME)[0]

args = {
    "detection": config_default["detection_model_path"],
    "input": config_default["input_stream"],
    "input_layer": "input_0",
    "labels": config_default["label_path"],
    "output_layer": "",
    "detect_roi": [
        config_default["detection_area_xmin"],
        config_default["detection_area_ymin"],
        config_default["detection_area_xmax"],
        config_default["detection_area_ymax"],
    ],
    "input_area": [
        config_default["input_area_xmin"],
        config_default["input_area_ymin"],
        config_default["input_area_xmax"],
        config_default["input_area_ymax"],
    ],
    "saved_detection_path": config_default["saved_detection_path"],
    "detection_threshold": config_default["detection_threshold"],
    "detect_buffer": detect_buffer,
    "last_image_deque": last_image_deque,
}


# create Flask & stream instance
app = flask.Flask(__name__)
stream = Stream(args)

device = DeviceInfo()

failed_batch_insert = []
failed_batch_insert_central = []


def insertDatabase():
    # print('\n\n')
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))

    global failed_batch_insert
    global failed_batch_insert_central

    duplicate_buffer = stream.getDetectBuffer()

    buffer = duplicate_buffer + failed_batch_insert
    buffer_central = duplicate_buffer + failed_batch_insert_central

    if len(buffer) > 0:
       if not database.batchInsert(buffer):
           if len(failed_batch_insert) < 50:
               failed_batch_insert += buffer
           else:
               print("max failed reached")
       else:
           failed_batch_insert = []

    if len(buffer_central) > 0:
        if not database_central.batchInsertCentral(buffer_central):
            if len(failed_batch_insert_central) < 50:
                failed_batch_insert_central += buffer_central
            else:
                print("max failed reached")
        else:
            failed_batch_insert_central = []


def timed_insert():
    print("insert")
    timeout = 10
    insert_thread = threading.Thread(target=insertDatabase)
    insert_thread.start()
    insert_thread.join(timeout)
    if insert_thread.is_alive():
        print("Execution timed out. Aborting.")
        insert_thread._stop()  # Metode ini tidak disarankan, tapi bisa digunakan dalam situasi tertentu.


scheduler = BackgroundScheduler()
scheduler.add_job(func=timed_insert, trigger="interval", seconds=12)


# Flask routes
@app.route("/")
def index():
    return flask.render_template("index.html", active_page="dashboard")


@app.route("/time", methods=["GET"])
def get_time():
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return flask.jsonify(formatted_time)


@app.route("/time", methods=["POST"])
def set_time():
    data = flask.request.get_json()
    # Mengubah format waktu
    client_time = datetime.strptime(data["time"], "%d/%m/%Y, %H:%M:%S")
    client_time = client_time.strftime("%Y-%m-%d %H:%M:%S")

    os.system(f'echo jetson | sudo -S date -s "{client_time}"')

    print(client_time)
    return flask.jsonify(data)


@app.route("/video_feed")
def video_feed():
    return flask.Response(
        stream.generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/setting")
def setting():
    return flask.render_template("setting.html", active_page="setting")


@app.route("/settings", methods=["GET"])
def settings():
    response = {
        "input_stream": config_default["input_stream"],
        "detect_roi": stream.detect_roi,
        "input_area": stream.input_area,
        "saved_detection_path": stream.saved_detection_path,
        "detection_model": config_default["detection_model_path"],
        "detection_threshold": config_default["detection_threshold"],
        "labels": config_default["label_path"],
    }
    return flask.jsonify(response)


@app.route("/save_settings", methods=["POST"])
def save_settings():
    try:
        response = {"status": "OK", "message": "Data berhasil disimpan"}
        return flask.jsonify(response)

    except Exception as e:
        error_data = {"status": "Error", "message": str(e)}
        return flask.jsonify(error_data)


@app.route("/save_roi_settings", methods=["POST"])
def save_roi_settings():
    try:
        data = {
            "detection_model_path": config_default["detection_model_path"],
            "label_path": config_default["label_path"],
            "saved_detection_path": stream.saved_detection_path,
            "detection_area_xmin": stream.detect_roi[0],
            "detection_area_ymin": stream.detect_roi[1],
            "detection_area_xmax": stream.detect_roi[2],
            "detection_area_ymax": stream.detect_roi[3],
            "input_area_xmin": stream.input_area[0],
            "input_area_ymin": stream.input_area[1],
            "input_area_xmax": stream.input_area[2],
            "input_area_ymax": stream.input_area[3],
            "detection_threshold": config_default["detection_threshold"],
            "input_stream": config_default["input_stream"],
        }
        database.update_config(Config.LOBBY_NAME, data)
        response = {"status": "OK", "message": "Data berhasil disimpan"}
        return flask.jsonify(response)

    except Exception as e:
        error_data = {"status": "Error", "message": str(e)}
        return flask.jsonify(error_data)


@app.route("/data")
def data():
    return flask.render_template("data.html", active_page="data")


@app.route("/datas/<string:date_from>/<string:date_to>", methods=["GET"])
def datas_get_last(date_from, date_to):
    try:
        # Perform the database query using the provided date range
        return database.select_detection_range(date_from, date_to)

    except Exception as e:
        error_data = {"status": "Error", "message": str(e)}
        return flask.jsonify(error_data)


@app.route("/datas_get_last/<int:num_datas>", methods=["GET"])
def get_last(num_datas):
    try:
        return database.get_data_last(num_datas)

    except Exception as e:
        error_data = {"status": "Error", "message": str(e)}
        return flask.jsonify(error_data)


@app.route("/get_image", methods=["POST"])
def get_image():
    try:
        data = flask.request.get_json()
        image_path = data["path"]
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            return flask.jsonify({"image": encoded_image})
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/get_deque", methods=["GET"])
def get_deque():
    try:
        list_image = list(stream.last_image_deque)
        array_image = []

        for item in list_image:
            image_path = item["image_path"]
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                obj = {
                    'gender' : item['gender'], 
                    'gender_score' : item['gender_score'],
                    'age' : item['age'],
                    'age_score' : item['age_score'],
                    'attr_headwear' : item['attr_headwear'], 
                    'attr_mask' : item['attr_mask'], 
                    'attr_glasses' : item['attr_glasses'], 
                    'img_name' : encoded_image, 
                    'timestamp' : item['timestamp'], 
                }
            array_image.append(obj)

            # print(item)
        return flask.jsonify({"deque": array_image})

        # data = flask.request.get_json()
        # image_path = data["path"]
        # with open(image_path, "rb") as image_file:
        #     encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
        #     return flask.jsonify({"image": encoded_image})
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/control", methods=["POST"])
def control():
    try:
        data = flask.request.get_json()
        if data["control"] == "roi_xmin":
            if int(data["value"]) >= stream.detect_roi[2]:
                stream.detect_roi[0] = stream.detect_roi[2] - 5

            else:
                stream.detect_roi[0] = int(data["value"])
        elif data["control"] == "roi_ymin":
            if int(data["value"]) >= stream.detect_roi[3]:
                stream.detect_roi[1] = stream.detect_roi[3] - 5
            else:
                stream.detect_roi[1] = int(data["value"])

        elif data["control"] == "roi_xmax":
            stream.detect_roi[2] = int(data["value"])

        elif data["control"] == "roi_ymax":
            stream.detect_roi[3] = int(data["value"])

        elif data["control"] == "input_xmin":
            if int(data["value"]) >= stream.input_area[2]:
                stream.input_area[0] = stream.input_area[2] - 5
            else:
                stream.input_area[0] = int(data["value"])

        elif data["control"] == "input_ymin":
            if int(data["value"]) >= stream.input_area[3]:
                stream.input_area[1] = stream.input_area[3] - 5
            else:
                stream.input_area[1] = int(data["value"])

        elif data["control"] == "input_xmax":
            stream.input_area[2] = int(data["value"])

        elif data["control"] == "input_ymax":
            stream.input_area[3] = int(data["value"])

        response = {"status": "OK", "message": "Data berhasil diproses"}
        return flask.jsonify(response)

    except Exception as e:
        error_data = {"status": "Error", "message": str(e)}
        return flask.jsonify(error_data)


# start stream thread
stream.start()
scheduler.start()
app.run(host="0.0.0.0", port=5000)

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
