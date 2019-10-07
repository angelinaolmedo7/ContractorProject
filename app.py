"""RanchoStop is a store focusing on a modern rebranding of Tarantulas."""
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

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


@app.route('/ranchos/<rancho_id>')
def ranchos_show(rancho_id):
    """Show a single listing."""
    rancho = ranchos.find_one({'_id': ObjectId(rancho_id)})
    return render_template('ranchos_show.html', rancho=rancho)
