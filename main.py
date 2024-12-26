from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import json
import numpy as np
import os
from datetime import timedelta

from flask_cors import CORS
app=Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.secret_key = 'aouu&&kkàànnééé&' 
app.config["SESSION_TYPE"] = "filesystem"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.permanent_session_lifetime = timedelta(days=5)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):  # Handle NumPy int64
            return int(obj)
        return super(CustomJSONEncoder, self).default(obj)

app.json_encoder = CustomJSONEncoder
CORS(app)
db=SQLAlchemy(app)
ma=Marshmallow(app)




