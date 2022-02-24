import pickle
import numpy as np

class MyModel:
    def __init__(self):
        self._model = pickle.load(open("model.pkl", "rb"))

    def predict(self, X):
        classes = ['Setosa','Versicolor','Virginica']
        float_features = [float(item) for item in X]
        features = [np.array(float_features)]
        prediction = int(self._model.predict(features))
        return classes[prediction]

f =['5.9','5.1','3.5','1.8']
model = MyModel()
print(model.predict(f))