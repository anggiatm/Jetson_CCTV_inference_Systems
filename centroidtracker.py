from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np

class CentroidTracker():
    def __init__(self, maxDisappeared=3):
        self.nextObjectID = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.classes = OrderedDict()
        self.rectangles = OrderedDict()
        self.scores = OrderedDict()  # Added for storing score information
        self.maxDisappeared = maxDisappeared
        self.lastObjectID = -1

    def register(self, centroid, class_id, rect, score):
        self.objects[self.nextObjectID] = centroid
        self.classes[self.nextObjectID] = class_id
        self.rectangles[self.nextObjectID] = rect
        self.scores[self.nextObjectID] = score  # Store score information
        self.disappeared[self.nextObjectID] = 0
        self.lastObjectID = self.nextObjectID
        self.nextObjectID += 1

    def deregister(self, objectID):
        del self.objects[objectID]
        del self.classes[objectID]
        del self.rectangles[objectID]
        del self.scores[objectID]  # Remove score information
        del self.disappeared[objectID]

    def update(self, rects, class_ids, scores):
        if len(rects) == 0:
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > self.maxDisappeared:
                    self.deregister(objectID)
            return self.objects, self.classes, self.rectangles, self.scores

        inputCentroids = np.zeros((len(rects), 2), dtype="int")

        for (i, (startX, startY, endX, endY)) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            inputCentroids[i] = (cX, cY)

        if len(self.objects) == 0:
            for i in range(0, len(inputCentroids)):
                self.register(inputCentroids[i], class_ids[i], rects[i], scores[i])
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())

            D = dist.cdist(np.array(objectCentroids), inputCentroids)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            usedRows = set()
            usedCols = set()

            for (row, col) in zip(rows, cols):
                if row in usedRows or col in usedCols:
                    continue

                objectID = objectIDs[row]
                self.objects[objectID] = inputCentroids[col]
                self.classes[objectID] = class_ids[col]
                self.rectangles[objectID] = rects[col]
                self.scores[objectID] = scores[col]  # Update score information
                self.disappeared[objectID] = 0

                usedRows.add(row)
                usedCols.add(col)

            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            if D.shape[0] >= D.shape[1]:
                for row in unusedRows:
                    objectID = objectIDs[row]
                    self.disappeared[objectID] += 1

                    if self.disappeared[objectID] > self.maxDisappeared:
                        self.deregister(objectID)
            else:
                for col in unusedCols:
                    self.register(inputCentroids[col], class_ids[col], rects[col], scores[col])

        return self.objects, self.classes, self.rectangles, self.scores

# Example usage:
# ct = CentroidTracker()

# # Assume rects_f is a list of rectangles and results is a list of dictionaries with 'class_id' and 'score' information
# objects, classes, rect, score = ct.update(rects_f, [result['class_id'] for result in results], [result['score'] for result in results])
