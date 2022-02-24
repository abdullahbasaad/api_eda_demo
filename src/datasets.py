from constants.http_status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from flask import Blueprint, request, make_response, render_template
from flask.json import jsonify
import validators
from db import Dataset, db
import numpy as np
from auth import requires_auth
from login import return_user
from globals import DATASETS, DATASETCOLUMNS
import pickle

datasets = Blueprint("datasets", __name__)

### Global User id will be extracted later from a token SSO
### ======================================================
global user_id
user_id = None

### Not used, maybe later we need to customize dataset
#  and store them in the cloud.
### ==================================================
@datasets.route('/import', methods=['POST', 'GET'])
@requires_auth
def handle_datasets():
    user_id = return_user()
    if user_id != None:
        if request.method == 'POST':
            body = request.get_json().get('body', '')
            url = request.get_json().get('url', '')

            if not validators.url(url):
                return jsonify({
                    'error': 'Enter a valid url'
                }), HTTP_400_BAD_REQUEST

            if Dataset.query.filter_by(url=url).first():
                return jsonify({
                    'error': 'URL already exists'
                }), HTTP_409_CONFLICT

            dataset = Dataset(url=url, body=body, user_id=user_id)
            db.session.add(dataset)
            db.session.commit()

            return jsonify({
                'id': dataset.id,
                'url': dataset.url,
                'visit': dataset.visits,
                'body': dataset.body,
                'created_at': dataset.created_at,
                'updated_at': dataset.updated_at,
            }), HTTP_201_CREATED
        else:
            datasets = Dataset.query.filter_by(user_id=user_id)

            data = []

            for dataset in datasets.items:
                data.append({
                    'id': dataset.id,
                    'url': dataset.url,
                    'visit': dataset.visits,
                    'body': dataset.body,
                    'created_at': dataset.created_at,
                    'updated_at': dataset.updated_at,
                })

            return jsonify({'data': data, "meta": dataset.body}), HTTP_200_OK

### Return a dataset specs. A function is built temporary 
#  maybe later we need to develop it.
### ==================================================
@datasets.route('/dataset specs/<int:id>', methods=['GET'])
@requires_auth
def get_dataset(id):
    user_id = return_user()
    if user_id != None:
        try:
            dataset = Dataset.query.filter_by(user_id=user_id, ds_id=id).first()
            return jsonify({
                'Dataset id': dataset.ds_id,
                'url': dataset.url,
                'visit': dataset.visits,
                'body': dataset.body,
                'created_at': dataset.created_at,
                'updated_at': dataset.updated_at,
            }), HTTP_200_OK
        except ValueError:
            return jsonify({"message": "No dataset"}), HTTP_404_NOT_FOUND
    else:
        return jsonify({"message": "No dataset"}), HTTP_404_NOT_FOUND

### Help function to check float values
### ==================================================
def isfloat(num) -> bool:
    try:
        float(num)
        return True
    except ValueError:
        return False

### Parsing update dataset values, it takes two param:
# 1- The request body
# 2- The dataset id
# Parse each field datatype and return a result, message
### =================================================
def parse_update_post(body, ds_id):
    message = ''
    for i, v  in body.items():
        if i not in list(DATASETCOLUMNS[ds_id][ds_id]):
            return False, f'Ivalid field name {i} does not exist in the dataset!.'
        else:
            for j, ct in DATASETCOLUMNS[ds_id][ds_id].items():
                if i == j and (ct == 'int' and isinstance(v, int)==False):
                    message = f'Data type of {i} should be integer'
                    break
                elif i == j and (ct == 'float' and (isinstance(v, float)== False  and isinstance(v, int)== False)):
                    message = f'Data type of {i} should be float'
                    print('here')
                    break
                elif i == j and (ct == 'str' and (isinstance(v, str) == False)):
                    message = f'Data type of {i} should be string'
                    break
    if message != '':
        return False, message  
    else:
        return True, message

### Endpoint to update a dataset values, it takes two param:
# 1- The collection id
# 2- The dataset id
# It parse the json object to verify the columns and their 
# values. It receives a json object with particular coulmns 
# and values need to update not just one value.
### =================================================
@datasets.route('/update/<int:ds_id>/<string:coll>', methods=['PUT'])
@requires_auth
def editdataset(ds_id, coll):
    user_id = return_user()
    if user_id != None:
        if ds_id< len(DATASETS):
            if coll in list(DATASETS[ds_id][ds_id].keys()):
                body = request.get_json()
                data = dict(body)
                result, message = parse_update_post(data, ds_id)
                if result:
                    for i, v in data.items():
                        DATASETS[ds_id][ds_id][coll][i] = v
                    return jsonify({'message': f'Collection has been updated {DATASETS[ds_id][ds_id][coll]}'}), HTTP_200_OK
                else:
                    return jsonify({'message': message}), HTTP_404_NOT_FOUND
            else:
                return jsonify({'message': 'Collection not found'}), HTTP_404_NOT_FOUND
        else:
            return jsonify({'message': 'Dataset not found'}), HTTP_404_NOT_FOUND

    return jsonify({'message': "You have to login first.."}), HTTP_200_OK

### Endpoint to update delete a dataset it takes one param:
# 1- The dataset id. Storing datasets is temporary while the
# session is life, not physically in the database. So the pop
# here just for data, the dataset itself will keep the index
# to avoid misordering the data with the other lists. But the
# dataset set specs will be deleted from the DB. 
### =================================================
@datasets.route("/delete/<int:ds_id>", methods=['DELETE'])
@requires_auth
def delete_dataset(ds_id):
    user_id = return_user()
    if user_id != None:
        if ds_id < len(DATASETS):
            dataset = Dataset.query.filter_by(user_id=user_id, ds_id=ds_id).first()

            if not dataset:
                return jsonify({'message': 'Dataset not found'}), HTTP_404_NOT_FOUND

            #DATASETS.pop(id)
            DATASETS[ds_id] = "Deleted"
            db.session.delete(dataset)
            db.session.commit()

            return jsonify({'message': 'Dataset has been deleted'}), HTTP_200_OK
        return jsonify({'message': 'Dataset not found'}), HTTP_404_NOT_FOUND
    return jsonify({'message': "You have to login first.."}), HTTP_200_OK

### Endpoint to update delete a collection from a dataset, it takes 
# two param:
# 1- The dataset id.
# 2- The collection id
### =================================================
@datasets.route("/delete collection/<int:ds_id>/<string:coll_id>", methods=['DELETE'])
@requires_auth
def delete_collection(ds_id, coll_id):
    user_id = return_user()
    if user_id != None:
        if ds_id < len(DATASETS):
            if coll_id in list(DATASETS[ds_id][ds_id].keys()):
                del DATASETS[ds_id][ds_id][coll_id]
                return jsonify({'message': 'A collection has been deleted successfully'}), HTTP_200_OK       
            return jsonify({'message': 'A collection does not exist in the dataset'}), HTTP_404_NOT_FOUND 
        return jsonify({'message': 'Dataset not found'}), HTTP_404_NOT_FOUND
    return jsonify({'message': "You have to login first.."}), HTTP_200_OK

### Endpoint to collect a statistics about the user
# how many times he visited a particular URL and other
# information. (just thoughs), maybe later will develop
# be developed.
### =================================================  
@datasets.route("/stats", methods=['GET'])
@requires_auth
def get_stats():

    user_id = return_user()
    if user_id != None:
        data = []
        items = Dataset.query.filter_by(user_id=user_id).all()

        for item in items:
            new_link = {
                'visits': item.visits,
                'url': item.url,
                'id': item.id,
            }

        data.append(new_link)

        return jsonify({'data': data}), HTTP_200_OK
    else:
        return jsonify({'message': "No login registered!.."}), HTTP_200_OK

### Help function to return a specifc datatype without
# a class name.
### =================================================  
def type_condition(v):
    if isinstance(v, str):
        return 'str'
    elif isinstance(v, int):
        return 'int'
    elif isinstance(v, float):
        return 'float'
    else:
        return type(v)

### Help function to return a number of a dataset
# observations. Here the dataset in the list has two 
# keys. One for a list because it stores in a list.
# and one for a dictionary, in case the list has more 
# than one datasets in a list. in both ways the dataset
# id and dictionary id are same to be easy in handling 
# them.
### ================================================= 
def return_collection_count(ds_id): # dataset
    col_count = 0
    
    for key in DATASETS[ds_id][ds_id].keys():
        col_count += 1
    return str(col_count + 1)

### Parsing new collection values, it takes two param:
# 1- The request body
# 2- The dataset id
# Parse each field datatype and return a result, message
### =================================================
def parse_new_collection_post(body, ds_id):
    message = ''

    if (np.array(body.keys()) == np.array(DATASETCOLUMNS[ds_id][ds_id].keys())).all() == False:
        return False, "Missing some fields or invalid field name!.."

    for i, v  in body.items():
        for j, ct in DATASETCOLUMNS[ds_id][ds_id].items():

            if i == j and (ct == 'int' and isinstance(v, int)==False):
                message = f'Data type of {i} should be integer'
                break
            elif i == j and (ct == 'float' and (isinstance(v, float)== False  and isinstance(v, int)== False)):
                message = f'Data type of {i} should be float'
                print('here')
                break
            elif i == j and (ct == 'str' and (isinstance(v, str) == False)):
                message = f'Data type of {i} should be string'
                break
    if message != '':
        return False, message  
    else:
        return True, message

### Endpoint to post a new parsed collection to the dataset
# it takes one param.
# 1- The dataset id
# Parse each field datatype and added to the dataset if
# parsed operation result is true.
### =================================================
@datasets.route("/dataset/post collection/<int:ds_id>", methods=["POST"])
@requires_auth
def create_col(ds_id): # Dataset id
    body = request.get_json()
    result, message = parse_new_collection_post(body,0)
    if ds_id < len(DATASETS):
        if result:
            col_cnt = return_collection_count(ds_id)
            DATASETS[ds_id][ds_id][col_cnt] = body
            res = make_response(jsonify({"Message": f"Collection created {col_cnt} {body}"}), HTTP_201_CREATED)
            return res
        else:
            res = make_response(jsonify({"Error":message}), HTTP_400_BAD_REQUEST)
            return res
    else:
        return jsonify({'message': 'Dataset not found'}), HTTP_404_NOT_FOUND

### To display a dataset in a json format
### ==================================================

@datasets.route("/dataset/show/<int:ds_id>", methods=['GET'])
@requires_auth
def show_dataset(ds_id):
    if ds_id < len(DATASETS):
        return jsonify ({'Dataset': DATASETS[ds_id]}), HTTP_200_OK
    return jsonify ({'message': 'No data..'}), HTTP_204_NO_CONTENT
            
### To Run a model
### ==================================================
model = pickle.load(open("model.pkl", "rb"))
@datasets.route("/predict", methods = ["POST"])
def predict():
    float_features = [float(x) for x in request.form.values()]
    features = [np.array(float_features)]
    prediction = int(model.predict(features))
    classes = ['Setosa','Versicolor','Virginica']
    return render_template("index.html", prediction_text = "The flower species is {}".format(classes[prediction]))


