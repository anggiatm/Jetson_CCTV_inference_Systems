(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD (Asynchronous Module Definition) support
        define(['exports'], function (exports) {
            root.setting = factory(exports);
        });
    } else if (typeof exports === 'object' && typeof module !== 'undefined') {
        // CommonJS (Node.js) support
        module.exports = factory({});
    } else {
        // Browser global
        root.setting = factory({});
    }
}(typeof self !== 'undefined' ? self : this, function (exports) {
    'use strict';

    function control(type){
        let value = document.getElementById(type).value;
        // console.log(value)
        const data = {
            control: type,
            value: value
        }
        fetch('/control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Server response:', data);
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });

        refresh_settings();
    }

    function save_roi_settings(){
        fetch('/save_roi_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: {},
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            refresh_settings()
            console.log('Server response:', data);
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
    }

    function save_settings(){
        const rtspUrl = document.getElementById('rtsp-url').value;
        const threshold = document.getElementById('threshold').value;
        const source_usb = document.getElementById('source-usb').checked;

        const data = {
            RTSP_URL: rtspUrl,
            threshold: parseFloat(threshold),
            source_usb: source_usb
        };

        fetch('/save_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            refresh_settings()
            console.log('Server response:', data);
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
    }

    function refresh_settings(){
        // play()
        fetch('/settings', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json', // Tentukan tipe konten sebagai JSON
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json(); // Jika server merespons dengan JSON, Anda dapat memprosesnya di sini
        })
        .then(data => {
            console.log('Server response:', data);
            document.getElementById('rtsp-url').value = data.input_stream;
            document.getElementById('threshold').value = data.detection_threshold;

            let input_x = document.getElementById('input_xmin');
            let input_y = document.getElementById('input_ymin');
            let input_w = document.getElementById('input_xmax');
            let input_h = document.getElementById('input_ymax');
            input_x.value = data.input_area[0]
            input_y.value = data.input_area[1]
            input_w.value = data.input_area[2]
            input_h.value = data.input_area[3]

            let roi_x = document.getElementById('roi_xmin');
            let roi_y = document.getElementById('roi_ymin');
            let roi_w = document.getElementById('roi_xmax');
            let roi_h = document.getElementById('roi_ymax');
            roi_x.value = data.detect_roi[0]
            roi_y.value = data.detect_roi[1]
            roi_w.value = data.detect_roi[2]
            roi_h.value = data.detect_roi[3]
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
    }

    function toggle_button(green, button_id, text){
        let button = document.getElementById(button_id);
        if (green){
            button.classList.remove('btn-outline-danger');
            button.classList.add('btn-outline-success');
        }
        else {
            button.classList.remove('btn-outline-success');
            button.classList.add('btn-outline-danger');
        }
        button.innerText = text;
    }

    // const play = () => {
    //     playStream(getWebsocketURL('output'), document.getElementById('video-player'));
    // };

    function capturing (){
        control('capturing');
        refresh_settings();
    }


    document.addEventListener('DOMContentLoaded', refresh_settings);

    exports.control = control;
    exports.capturing = capturing;
    exports.save_settings = save_settings;
    exports.save_roi_settings = save_roi_settings;
    return exports;
}));