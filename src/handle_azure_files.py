import os
import yaml
import pandas as pd
import csv
import json
import pandas as pd 
import numpy as np
from db import Dataset, db, User
from constants.http_status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST
from azure.storage.blob import BlobServiceClient
from auth import requires_auth
from flask import Blueprint, jsonify
from globals import DATASETS, DATASETCOLUMNS
from datetime import datetime
from login import return_user
import logging
from azure.core.exceptions import (
    ResourceNotFoundError,
    ResourceExistsError,
    ClientAuthenticationError)

files = Blueprint("files", __name__)
global user_id
user_id = None

AZURE_STORAGE_CONNECTIONSTRING = os.environ.get("AZURE_STORAGE_CONNECTIONSTRING")
DATASET_CONTAINER_NAME = os.environ.get("DATASET_CONTAINER_NAME")
AZURE_ACCOUNT_KEY = os.environ.get("AZURE_ACCOUNT_KEY")

### Create a temporary json object in the API path. 
#  the function receives a dataset CSV file from the
# source, it creates a json object, dataset dictionary,
# and return a number of obseravtions. This function
# calls a nother function to update the dataype of
# the dataset according to the CSV datafram dictionary.
### ==================================================
def make_json(csv_file, ds_id):
    data = {}
    data_id = {}
    counter = 0
    with open(csv_file, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)
        for i, rows in enumerate(csvReader):
            counter = i+1
            data[i+1] = rows # to start rows from 1 in the datasaet.
            
    with open('./jsn.json', 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps(data, indent=4))

    with open('./jsn.json') as f:
        data = json.load(f)
        data_id[ds_id] = data

    cleaned_data = correct_dataset_datatypes(data, ds_id)
    data_id[ds_id] = cleaned_data

    DATASETS.append(data_id)
    return counter 

### Extract column datatypes and store them with the
# dataset id in the separate doctionary in a list of
# all datatypes dictionarries of all datasets.
### ==================================================
def parse_columns(df, ds_id)-> None:
    datatypes={}
    temp_dic= {}
    
    for col in df.columns:
        if df[col].dtype == np.float64:
            temp_dic[col] = 'float'
        elif df[col].dtype == np.int64:
            temp_dic[col] = 'int'
        elif df[col].dtype == np.object0:
            temp_dic[col] = 'str'
        elif df[col].dtype == np.datetime64:
            temp_dic[col] = 'datetime' 
    datatypes[ds_id] = temp_dic
    DATASETCOLUMNS.append(datatypes)

### To display a dataset's metadata in a json format
### ==================================================
@files.route("/blob/metadata", methods = ["GET"])
#@files.get('/blob/metadata')
@requires_auth
def get_metadata():
    user_id = return_user()
    if user_id != None:
        user = User.query.filter_by(id=user_id).first()

        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTIONSTRING)
        container = blob_service_client.get_container_client(container=DATASET_CONTAINER_NAME)
        blob_list = container.list_blobs()
    
        for blob in blob_list:
            blob_client = blob_service_client.get_blob_client(container=DATASET_CONTAINER_NAME, blob="titanic.csv")
            a=blob_client.get_blob_properties()

            metadata = {"url": blob_client.url,
                        "blob_type" : blob.blob_type,
                        "last_modified":blob.last_modified,
                        "user": user.email,
                        "archive_status": blob.archive_status,
                        "userid": user_id,
                        "metadata": blob.metadata}
            break
   
        return jsonify({"metadata": metadata}), HTTP_200_OK
    else:
        return jsonify({"message": "You need to login first.! "}), HTTP_400_BAD_REQUEST

### To load a configuration of Auth0 settings and other 
# paths
### ==================================================
def load_config():
    dir_root = os.path.dirname(os.path.abspath(__file__))
    with open(dir_root + "/config.yaml", "r") as yamlfile:
        return yaml.load(yamlfile, Loader=yaml.FullLoader)

### Helping function to access a particular file in the
# directory.
# paths
### ==================================================
def get_files(dir):
    with os.scandir(dir) as entries:
        for entry in entries:
            if entry.is_file() and not entry.name.startwith('.'):
                yield entry

### Endpoint to importing a CSV file from Azure blob storage.
# the file name is a hard code for now. Later I will receive it
# from the UI. The function calls make_json to store a dataset
# temporary in the API with creating different dictionaries to
# help dealing with a dataset. It returns a json format with
# some information about the dataset and the number of observation
### ==================================================
@files.route("/import/dataset", methods = ["GET"])
#@files.get('/import/dataset')
@requires_auth
def download():
    ds_id = 0
    file_name="titanic.csv"
    user_id = return_user()
    if user_id != None:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTIONSTRING)
        container_client = blob_service_client.get_container_client(DATASET_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(file_name)

        with open(file_name, "wb") as f:
            data = blob_client.download_blob()
            data.readinto(f)
        
        df = pd.read_csv(file_name) 
        if len(DATASETS) == 0 or None:
            ds_id = 0  
        else:
            ds_id = len(DATASETS)
        
        parse_columns(df, ds_id)
        oberve_count = make_json(file_name, ds_id) 
        
        #os.remove(file_name)

        dataset = Dataset(url=blob_client.url, body='body', user_id=user_id, ds_id=ds_id)
        db.session.add(dataset)
        db.session.commit()
        
        return jsonify ({"Message ":f"{file_name} dataset has been imported successfully",
                         "Dataset id = ":f"Use this id '{ds_id}' to access the dataset",
                         "Source ":blob_client.url,
                         "Observation count": oberve_count}), HTTP_200_OK
    else:
        return jsonify({"message": "You need to login first.! "}), HTTP_400_BAD_REQUEST 

### Endpoint to upload a blob into the Azure blob storage.
# curentelly it uses a file in the same path to upload it.
# Later we need to read from a specific pathe to pick the file
# then upload it into Azure storage.
### ==================================================
#@files.post('/upload/blob')
@files.route("/upload/blob", methods = ["POST"])
@requires_auth
def upload():
    user_id = return_user()
    if user_id != None:
        try:
            client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTIONSTRING, logging_enable=True)
            cont_client = client.get_container_client(DATASET_CONTAINER_NAME)

            print("Uploading files underprocess...")
            file_name = 'iris.csv'
            upload_file_path = os.path.join('./', file_name) 
            blob_client = cont_client.get_blob_client(blob=file_name)
        except ClientAuthenticationError:
            return jsonify ({"message": "Client authentication error.."})

        metadata = {"x-ms-meta-name": "test",
                    "userid": user_id,
                    "access_level": "public",
                    "licence_mode": "cc3.0",
                    "created_at":  datetime.now()}

        try:
            cont_client.get_container_properties()
        except ResourceNotFoundError:
            cont_client.create_container()
    
        try:    
            with open(upload_file_path, "rb") as data:
                blob_client.upload_blob(data)
        except ResourceExistsError:
            return jsonify ({"message": "Blob is alredy existed"})

        return jsonify ({'message' : f'{file_name}  has beenn uploaded to the blob storage'})
    else:
        return jsonify({"message": "You need to login first.! "}), HTTP_400_BAD_REQUEST 

### Helping function to generate an importing log file, in case
# some errors hapened while reading the source file.
### ==================================================
def correct_dataset_datatypes(data, ds_id):
    count = 0
    for v in data.values():
        for i, dt in DATASETCOLUMNS[ds_id][ds_id].items():
            try:
                if dt == 'int':
                    v[i] = int(v[i])
                elif dt == 'float':
                    v[i] = float(v[i])
            except:
                logging.basicConfig(filename="importing_log.log", level=logging.INFO)
                logging.info(f"There are {count} observations the system can not handle them:")
                logging.info("===============================================================")
                logging.info(f'Invalid data, can not convert {i} data type to {dt} data type')
    return data





