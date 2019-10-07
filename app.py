"""RanchoStop is a store focusing on a modern rebranding of Tarantulas."""
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient

client = MongoClient()
db = client.RanchoStop
ranchos = db.ranchos

app = Flask(__name__)


@app.route('/')
def index():
    """Return homepage."""
    return render_template('index.html', ranchos=ranchos.find())


@app.route('/ranchos/new')
def playlists_new():
    """Create a new listing."""
    return render_template('new_listing.html')


@app.route('/ranchos', methods=['POST'])
def listing_submit():
    """Submit a new listing."""
    listing = {'title': request.form.get('title'),
               'species': request.form.get('species'),
               'description': request.form.get('description')
               }
    ranchos.insert_one(listing)
    return redirect(url_for('index'))
