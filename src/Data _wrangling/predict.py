import os
import warnings
import sys
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import ElasticNet
from urllib.parse import urlparse
import mlflow
import mlflow.sklearn
from sqlalchemy import column
from Data_Wrangling import Data_wrangling
import logging


logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)


def eval_metrics(actual, pred):
    rmse = np.sqrt(mean_squared_error(actual, pred))
    mae = mean_absolute_error(actual, pred)
    r2 = r2_score(actual, pred)
    return rmse, mae, r2


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    np.random.seed(40)

    # Read the titanic csv file from Azure blob storing
    try:
        data = pd.read_csv('titanic.csv')
    except Exception as e:
        logger.exception(
            "Unable to download the blob CSV file, please check the internet connection or Azure credential authority. Error: %s", e
        )

    dw = Data_wrangling(data)
    df, cat_col = dw.check_categorical_variables()
    #mis_col = dw.return_columns_has_missing_values()
    #df = dw.exclude_features_with_high_missing_values()
    
    df.to_csv('new_csv.csv')