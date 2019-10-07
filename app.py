"""RanchoStop is a store focusing on a modern rebranding of Tarantulas."""
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

host = os.environ.get('MONGODB_URI', 'mongodb://localhost:27019/RanchoStop')
client = MongoClient(host=f'{host}?retryWrites=false')
db = client.get_default_database()
ranchos = db.ranchos
comments = db.comments

app = Flask(__name__)


@app.route('/')
def index():
    """Return homepage."""
    return render_template('index.html', ranchos=ranchos.find())


@app.route('/ranchos/new')
def ranchos_new():
    """Create a new listing."""
    return render_template('new_listing.html', rancho={}, title='New Listing')


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
    listing_comments = comments.find({'rancho_id': ObjectId(rancho_id)})
    return render_template('ranchos_show.html', rancho=rancho,
                           comments=listing_comments)


@app.route('/ranchos/<rancho_id>/edit')
def ranchos_edit(rancho_id):
    """Show the edit form for a listing."""
    rancho = ranchos.find_one({'_id': ObjectId(rancho_id)})
    return render_template('ranchos_edit.html', rancho=rancho,
                           title='Edit Listing')


@app.route('/ranchos/<rancho_id>', methods=['POST'])
def ranchos_update(rancho_id):
    """Submit an edited listing."""
    updated_listing = {
        'title': request.form.get('title'),
        'species': request.form.get('species'),
        'description': request.form.get('description')
    }
    ranchos.update_one(
        {'_id': ObjectId(rancho_id)},
        {'$set': updated_listing})
    return redirect(url_for('ranchos_show', rancho_id=rancho_id))


@app.route('/ranchos/<rancho_id>/delete', methods=['POST'])
def ranchos_delete(rancho_id):
    """Delete one listing."""
    ranchos.delete_one({'_id': ObjectId(rancho_id)})
    return redirect(url_for('index'))


@app.route('/ranchos/comments', methods=['POST'])
def comments_new():
    """Submit a new comment."""
    comment = {
        'title': request.form.get('title'),
        'content': request.form.get('content'),
        'rancho_id': ObjectId(request.form.get('rancho_id'))
    }
    comment_id = comments.insert_one(comment).inserted_id
    return redirect(url_for('ranchos_show',
                            rancho_id=request.form.get('rancho_id')))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
