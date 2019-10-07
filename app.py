"""RanchoStop is a store focusing on a modern rebranding of Tarantulas."""
from flask import Flask, render_template, request
import os
from rancho import Rancho

host = os.environ.get

app = Flask(__name__)


@app.route('/')
def index():
    """Return homepage."""
    ranchos = [
        Rancho('Tarantula', 'Spider', 5),
        Rancho('Other Tarantula', 'Also a Spider', 7)
    ]
    return render_template('index.html', ranchos=ranchos)
