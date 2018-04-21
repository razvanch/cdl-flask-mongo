from bson import json_util
from bson.objectid import ObjectId
from flask import Flask, request
from flask_pymongo import PyMongo
from flask_cors import CORS
import pymongo


app = Flask(__name__)
CORS(app, supports_credentials=True)
mongo = PyMongo(app)

with app.app_context() as c:
    # DB setup / cleanup
    pass


def safe_object_id(code):
    try:
        return ObjectId(code)
    except:
        return None

# Example usage: check_fields(json_body, ['email', 'first_name', 'last_name'])
def check_fields(required_fields, given_fields):
    return set(required_fields) == set(given_fields)


@app.route('/authors', methods=['GET', 'POST'])
def authors():
    return '', 405

@app.route('/authors/<author_id>', methods=['GET', 'PATCH', 'DELETE'])
def author(author_id):
    return '', 405

@app.route('/posts', methods=['GET', 'POST'])
def posts():
    return '', 405

@app.route('/posts/<post_id>', methods=['GET', 'PATCH', 'DELETE'])
def post(post_id):
    return '', 405

@app.route('/login', methods=['POST'])
def login():
    return '', 405
