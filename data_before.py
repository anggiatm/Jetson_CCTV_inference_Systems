# import
from jetson_inference import imageNet
import os

# load model
gender_model_path = "/home/jetson/app/model/classification/gender.onnx"
gender_label_path = "/home/jetson/app/model/classification/gender.txt"
age_male_model_path = "/home/jetson/app/model/classification/age_male.onnx"
age_male_label_path = "/home/jetson/app/model/classification/age_male.txt"
age_female_model_path = "/home/jetson/app/model/classification/age_female.onnx"
age_female_label_path = "/home/jetson/app/model/classification/age_female.txt"
input_layer = "input_0"
output_layer = "output_0"

gender_model = imageNet(
    model=gender_model_path,
    labels=gender_label_path,
    input_blob=input_layer,
    output_blob=output_layer,
)
age_male_model = imageNet(
    model=age_male_model_path,
    labels=age_male_label_path,
    input_blob=input_layer,
    output_blob=output_layer,
)
age_female_model = imageNet(
    model=age_female_model_path,
    labels=age_female_label_path,
    input_blob=input_layer,
    output_blob=output_layer,
)

# loop through folders

for root, _, files in os.walk("capture"):
    for filename in files:
        if filename.endswith((".jpg", ".jpeg", ".png")):
            image_path = os.path.join(root, filename)

            print(image_path)

# parsing path
# day, month, year, hour, minute, second

# inference model geder

# if age = 0 FEMALE
# inference female age model

# to buffer

# if age = 1 Male
# inference age model

# to buffer
