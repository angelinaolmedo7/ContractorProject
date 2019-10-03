"""RanchoStop is a store focusing on a modern rebranding of Tarantulas."""
from flask import Flask, render_template, request
import rancho

app = Flask(__name__)


@app.route('/')
def index():
    """Return homepage."""
    return render_template('index.html')
