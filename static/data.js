(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD (Asynchronous Module Definition) support
        define(['exports'], function (exports) {
            root.core = factory(exports);
        });
    } else if (typeof exports === 'object' && typeof module !== 'undefined') {
        // CommonJS (Node.js) support
        module.exports = factory({});
    } else {
        // Browser global
        root.data = factory({});
    }
}(typeof self !== 'undefined' ? self : this, function (exports) {
    'use strict';

     function show(path, id){
        fetch('/get_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ path: path }),
        }).then(response =>{
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        }).then(data => {
            //console.log('Server response:', data);
            const img = new Image();
            img.src = 'data:image/jpeg;base64,' + data.image;
            img.style = 'height:100px'
            document.getElementById('image-container-' + id).innerHTML = '';
            document.getElementById('image-container-'+id).appendChild(img);
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
    }

    function refresh_datas(date_from, date_to){
        console.log(date_from);
        console.log(date_to);

        fetch('/datas/' + date_from + '/' + date_to, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json', // Tentukan tipe konten sebagai JSON
            },
            // body: JSON.stringify({ date_from: date_from, date_to: date_to}),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json(); // Jika server merespons dengan JSON, Anda dapat memprosesnya di sini
        })
        .then(data => {
            // console.log(data)
            data = data.reverse();
            const main_table = document.getElementById('main-table');
            main_table.innerHTML = '';
            data.forEach(obj => {
                let classes = "";
                switch(obj.class_id) {
                    case 1:
                        classes = "L"
                        break;
                    case 2:
                        classes = "P"
                        break;
                    case 3:
                        classes = "LT"
                        break;
                    case 4:
                        classes = "PH"
                        break;
                    case 5:
                        classes = "LA"
                        break;
                    case 6:
                        classes = "PA"
                        break;

                    default:
                        classes = "Unknown"
                }
                const row = main_table.insertRow();
                show(obj.image_path, obj.id)
                row.innerHTML = `
                <td>${obj.id}</td>
                <td>${obj.timestamp.split(" ")[1]}</td>
                <td>${classes}</td>
                <td>${obj.score}</td>
                <td><div id="image-container-${obj.id}"></div></td>`;
            });

            const count_table = document.getElementById('count-table');
            count_table.innerHTML = '';
            

            for(let i=1; i<=6; i++){
                const row = count_table.insertRow();
                let val = data.filter(function(obj) {
                    return obj.class_id === i;
                }).length;

                let classes = "";
                switch(i) {
                    case 1:
                        classes = "L"
                        break;
                    case 2:
                        classes = "P"
                        break;
                    case 3:
                        classes = "LT"
                        break;
                    case 4:
                        classes = "PH"
                        break;
                    case 5:
                        classes = "LA"
                        break;
                    case 6:
                        classes = "PA"
                        break;

                    default:
                        classes = "Unknown"
                }

                row.innerHTML = `
                <th scope="row">${classes}</th>
                <td>${val}</td>`;
            }
            const row = count_table.insertRow();
            row.innerHTML = `
                <th scope="row">TOTAL</th>
                <td>${data.length}</td>`;
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
    }

    function init(){
        $('.date_from').dateAndTime()
        $('.date_to').dateAndTime()

        let date = get_now();
        refresh_datas(date+" 00:00:00", date+" 23:59:59");

        document.querySelector('input[type="date"].date_from').value = date
        document.querySelector('input[type="time"].date_from').value = "00:01"
        document.querySelector('input[type="date"].date_to').value = date
        document.querySelector('input[type="time"].date_to').value = "23:59"
    }

    function get_now(){
        let today = new Date();
        let year = today.getFullYear();
        let month = ('0' + (today.getMonth() + 1)).slice(-2); // Tambahkan 1 karena bulan dimulai dari 0
        let day = ('0' + today.getDate()).slice(-2);
        let date = year + '-' + month + '-' + day;
        return date;
    }

    function handle_submit(){
        let date_from = document.querySelector('input[type="date"].date_from').value;
        let time_from = document.querySelector('input[type="time"].date_from').value;

        let date_to = document.querySelector('input[type="date"].date_to').value;
        let time_to = document.querySelector('input[type="time"].date_to').value;

        if (date_from || date_to != "") {
            refresh_datas(date_from + " " + time_from, date_to + " " + time_to)
        }
    }

    document.addEventListener('DOMContentLoaded', init());

    exports.show = show;
    exports.handle_submit = handle_submit;

    return exports;
}));
