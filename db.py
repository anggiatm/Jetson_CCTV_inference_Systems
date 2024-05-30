import mysql.connector
from flask import jsonify
from config import Config

import datetime

class DB:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connect()
        
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
            )
            self.cursor = self.connection.cursor()
            print("Connected to MySQL")
            # return True
        except mysql.connector.Error as e:
            print(f"Error connecting to MySQL: {e}")

    def insert_detected_object(self, id, gender, gender_score, age, age_score, attr_headwear, attr_mask, attr_glasses, image_path, timestamp):
        try:
            self.cursor.execute(
                """INSERT INTO detected_objects (id, gender, gender_score, age, age_score, attr_headwear, attr_mask, attr_glasses, image_path, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (id, gender, gender_score, age, age_score, attr_headwear, attr_mask, attr_glasses, image_path, timestamp),
            )
            self.connection.commit()
        except mysql.connector.Error as e:
            print(f"Error inserting detected object: {e}")
            self.connect()

    def get_data_last(self, num_datas):
        current_date = datetime.datetime.now().strftime('%d%m%Y')
        table_name = f"detected_{current_date}"

        try:
            query = f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT {num_datas}"
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            result = []

            

            for row in rows:
                obj = {
                    "id" : row[0],
                    "gender" : row[1],
                    "gender_score" : row[2],
                    "age" : row[3],
                    "age_score" : row[4],
                    "attr_headwear" : row[5],
                    "attr_mask" : row[6],
                    "attr_glasses" : row[7],
                    "image_path" : row[8],
                    "timestamp" : row[9].strftime("%Y-%m-%d %H:%M:%S"),
                }
                result.append(obj)

            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)})


    def batchInsert(self, data):
        try:
            # Get the current date in the format 'ddmmyyyy'
            current_date = datetime.datetime.now().strftime('%d%m%Y')
            table_name = f"detected_{current_date}"

            # Create the table if it doesn't exist
            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    gender INT,
                    gender_score INT,
                    age INT,
                    age_score INT,
                    attr_headwear INT,
                    attr_mask INT,
                    attr_glasses INT,
                    image_path VARCHAR(255),
                    timestamp TIMESTAMP
                )
            """
            self.cursor.execute(create_table_query)
            self.connection.commit()

            records = []
            for entry in data:
                
                gender = entry.get('gender')
                gender_score = entry.get('gender_score')
                age = entry.get('age')
                age_score = entry.get('age_score')
                attr_headwear = entry.get('attr_headwear')
                attr_mask = entry.get('attr_mask')
                attr_glasses = entry.get('attr_glasses')
                image_path = entry.get('image_path')
                timestamp = entry.get('timestamp')

                record = (gender, gender_score, age, age_score, attr_headwear, attr_mask, attr_glasses, image_path, timestamp)
                records.append(record)

            insert_query = f"""
                INSERT INTO {table_name} (gender, gender_score, age, age_score, attr_headwear, attr_mask, attr_glasses, image_path, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            self.cursor.executemany(insert_query, records)
            self.connection.commit()
            print(f"Batch insert successful into table {table_name}.")
            return True

        except Exception as e:
            print(f"Error during batch insert: {str(e)}")
            self.connect()
            return False
            # raise

    def batchInsertCentral(self, data):
        try:
            # Get the current date in the format 'ddmmyyyy'
            current_date = datetime.datetime.now().strftime('%y%m%d')
            partition_id = int(current_date)

            records = []
            for entry in data:
                gender_id = entry.get('gender')
                age_id = entry.get('age')
                timestamp = entry.get('timestamp')

                record = (Config.DEVICE_ID, gender_id, age_id, partition_id, timestamp)
                records.append(record)

            insert_query = f"""
                INSERT INTO visitors (device_id, gender_id, age_id, partition_id, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """

            self.cursor.executemany(insert_query, records)
            self.connection.commit()
            print(f"Batch insert successful into table central database.")
            return True

        except Exception as e:
            print(f"Error during batch insert: {str(e)}")
            self.connect()
            return False
            # raise

    def select_all(self, table):
        try:
            self.cursor.execute("SELECT * FROM " + table)
            rows = self.cursor.fetchall()
            result = []
            for row in rows:
                obj = {
                    "id" : row[0],     
                    "gender" : row[1],
                    "gender_score" : row[2],
                    "age" : row[3],
                    "age_score" : row[4],
                    "attr_headwear" : row[5],
                    "attr_mask" : row[6],
                    "attr_glasses" : row[7],
                    "image_path" : row[8],
                    "timestamp" : row[9].strftime("%Y-%m-%d %H:%M:%S"),
                }
                result.append(obj)
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)})

    def select_detection_range(self, date_from, date_to):
        dd = date_from.split(' ')[0].split('-')[2]
        mm = date_from.split(' ')[0].split('-')[1]
        yyyy = date_from.split(' ')[0].split('-')[0]
        table_name = "detected_"+dd+mm+yyyy

        try:
            query = "SELECT * FROM "+ table_name +" WHERE timestamp BETWEEN %s AND %s"
            #print(query)
            self.cursor.execute(query, (date_from, date_to))
            rows = self.cursor.fetchall()
            result = []

            for row in rows:
                obj = {
                    "id" : row[0],     
                    "gender" : row[1],
                    "gender_score" : row[2],
                    "age" : row[3],
                    "age_score" : row[4],
                    "attr_headwear" : row[5],
                    "attr_mask" : row[6],
                    "attr_glasses" : row[7],
                    "image_path" : row[8],
                    "timestamp" : row[9].strftime("%Y-%m-%d %H:%M:%S"),
                }
                result.append(obj)

            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)})

    def get_config(self, profile):
        try:
            self.cursor.execute(
                "SELECT * FROM config where id='" +profile+ "'"
            )
            rows = self.cursor.fetchall()
            names = [i[0] for i in self.cursor.description]
            
            result = []
            for row in rows:
                obj = {}
                for index, name in enumerate(names):
                    obj[name] = row[index]
                result.append(obj)

            return result
        except Exception as e:
            return {"error": str(e)}

    def update_config(self, profile_id, data):
        try:
            # Build the SQL query using parameterized query
            sql_query = """
                UPDATE config
                SET
                    detection_model_path = %s,
                    label_path = %s,
                    saved_detection_path = %s,
                    detection_area_xmin = %s,
                    detection_area_ymin = %s,
                    detection_area_xmax = %s,
                    detection_area_ymax = %s,
                    input_area_xmin = %s,
                    input_area_ymin = %s,
                    input_area_xmax = %s,
                    input_area_ymax = %s,
                    detection_threshold = %s,
                    input_stream = %s,
                    output_stream = %s
                WHERE
                    id = %s
            """

            # Execute the query with parameter values
            self.cursor.execute(sql_query, (
                data['detection_model_path'],
                data['label_path'],
                data['saved_detection_path'],
                data['detection_area_xmin'],
                data['detection_area_ymin'],
                data['detection_area_xmax'],
                data['detection_area_ymax'],
                data['input_area_xmin'],
                data['input_area_ymin'],
                data['input_area_xmax'],
                data['input_area_ymax'],
                data['detection_threshold'],
                data['input_stream'],
                data['output_stream'],
                profile_id
            ))

            # Commit the changes to the database
            self.connection.commit()

            return {"status": "OK", "message": "Data berhasil diperbarui"}

        except Exception as e:
            return {"status": "Error", "message": str(e)}
