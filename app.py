"""RanchoStop is a store focusing on a modern rebranding of Tarantulas."""
from flask import Flask, render_template, request
import os
from pymongo import MongoClient
from rancho import Rancho

client = MongoClient()
db = client.RanchoStop
ranchos = db.ranchos

app = Flask(__name__)


@app.route('/')
def index():
    """Return homepage."""
    return render_template('index.html', ranchos=ranchos.find())
