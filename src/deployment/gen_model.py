from sklearn.model_selection import train_test_split
from  sklearn import  datasets
import numpy as np
import sklearn
import pickle
import warnings
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from urllib.parse import urlparse
import mlflow
import mlflow.sklearn
import pickle
import logging
from mlflow.tracking import MlflowClient

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    #np.random.seed(40)
    
    iris=datasets.load_iris()
    x=iris.data
    y=iris.target

    # Split the dataset into train and test
    X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=50)
    
    sepal_length = float(sys.argv[0]) if len(sys.argv) > 1 else 5.9
    sepal_width = float(sys.argv[1])  if len(sys.argv) > 1 else 3
    petal_length = float(sys.argv[2]) if len(sys.argv) > 1 else 5.1
    petal_width = float(sys.argv[3])  if len(sys.argv) > 1 else 1.8
    
    with mlflow.start_run():

        # Instantiate the model
        from sklearn import tree
        classifier = tree.DecisionTreeClassifier()
        # Fit the model
        classifier.fit(X_train, y_train)
        predicted_qualities = classifier.predict(X_test)

        pickle.dump(classifier, open("model.pkl", "wb"))

        #print("Classification model (Sepal_length=%f, Sepal_width=%f,Petal_length=%f,Petal_width=%f ):" % (sepal_length, sepal_width, petal_length, petal_width))
        predictions=classifier.predict(X_test)
        accuracy = sklearn.metrics.accuracy_score(y_test,predictions)
        print("  ACURRACY: %s" % accuracy)

        mlflow.log_param("Sepal_length", sepal_length)
        mlflow.log_param("Sepal_width", sepal_width)
        mlflow.log_param("Petal_length", petal_length)
        mlflow.log_param("Petal_width", petal_width)

        mlflow.log_metric("Accuracy", accuracy)

        tracking_url_type_store = urlparse(mlflow.get_tracking_uri()).scheme

        # Model registry does not work with file store
        if tracking_url_type_store != "file":
            mlflow.sklearn.log_model(classifier, "model", registered_model_name="Model-A")
        else:
            mlflow.sklearn.log_model(classifier, "model")