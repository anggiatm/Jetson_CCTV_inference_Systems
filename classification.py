from jetson_inference import imageNet
class Classification:
    def __init__(self, model, labels='', input_layer='', output_layer=''):
        self.net = imageNet(model=model, labels=labels, input_blob=input_layer, output_blob=output_layer)

    def Process(self, img):
        return self.net.Classify(img)
