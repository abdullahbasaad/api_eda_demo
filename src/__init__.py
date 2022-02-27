from flask.json import jsonify
from constants.http_status_codes import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK
from flask import Flask, render_template, request
import numpy as np
import os
from login import login_auth
from datasets import datasets
from db import db
from flask_jwt_extended import JWTManager
from handle_azure_files import files
from auth import AuthError
import pickle

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SECRET_KEY"),
            SQLALCHEMY_DATABASE_URI= 'postgresql+psycopg2://postgres:abd1234@192.168.0.208:5432/api_demo',
            #os.environ.get("SQLALCHEMY_DB_URI_DEMO"),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY'),

            SWAGGER={
                'title': "Antser API Demo",
                'uiversion': 3
            }
        )
    else:
        app.config.from_mapping(test_config)

    db.app = app
    db.init_app(app)

    with app.app_context():
        db.create_all()

    JWTManager(app)
    app.register_blueprint(login_auth)
    app.register_blueprint(datasets)
    app.register_blueprint(files)

    model = pickle.load(open("model.pkl", "rb"))

    @app.route("/")
    def Home():
        return render_template("index.html")

    @app.route("/predict", methods = ["POST"])
    def predict():
        float_features = [float(x) for x in request.form.values()]
        features = [np.array(float_features)]
        prediction = model.predict(features)
        return render_template("index.html", prediction_text = "The flower species is {}".format(prediction))

    @app.errorhandler(HTTP_404_NOT_FOUND)
    def handle_404(e):
        return jsonify({'error': 'Not found'}), HTTP_404_NOT_FOUND

    @app.errorhandler(AuthError)
    def handle_auth_error(ex):
        response = jsonify(ex.error)
        response.status_code = ex.status_code
        return response

    return app