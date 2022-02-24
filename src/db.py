from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, onupdate=datetime.now())
    datasets = db.relationship('Dataset', backref="user")

    def __repr__(self) -> str:
        return 'User>>> {self.username}'

class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ds_id = db.Column(db.Text, nullable=False)
    body = db.Column(db.String(), nullable=True)
    url = db.Column(db.Text, nullable=False)
    visits = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, onupdate=datetime.now())

    def __repr__(self) -> str:
        return 'Dataset>>> {self.url}'