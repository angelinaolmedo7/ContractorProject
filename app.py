"""RanchoStop is a store focusing on a modern rebranding of Tarantulas."""
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from datetime import datetime
from flask_session import Session

host = os.environ.get('MONGODB_URI', 'mongodb://localhost:27019/RanchoStop')
client = MongoClient(host=f'{host}?retryWrites=false')
db = client.get_default_database()
users = db.users
ranchos = db.ranchos
listings = db.listings
comments = db.comments

app = Flask(__name__)

SESSION_TYPE = 'mongodb'
app.config.from_object(__name__)
Session(app)


@app.route('/')
def home():
    """Return listings homepage."""
    return render_template('home.html', user=session['user'])


# ---------------------------LOGIN---------------------------
@app.route('/login')
def login():
    """Login from."""
    return render_template('login.html')


@app.route('/login/submit', methods=['POST'])
def login_submit():
    """Login submit."""
    user = users.find_one({'username': request.form.get('username')})
    print(user['username'])
    if user is None:
        return redirect(url_for('login'))
    if user['password'] != request.form.get('password'):
        return redirect(url_for('login'))
    session['user'] = user
    return redirect(url_for('home', user=session['user']))


# ---------------------------USERS---------------------------
@app.route('/users/new')
def users_new():
    """Return a user creation page with starter Ranchos."""
    return render_template('new_user.html', user={}, title='New User')


@app.route('/users/directory')
def users_directory():
    """Return a directory of users."""
    return render_template('users_directory.html', users=users.find())


@app.route('/users', methods=['POST'])
def users_submit():
    """Submit a new user."""
    user = {'username': request.form.get('username'),
            'password': request.form.get('password'),
            'bio': request.form.get('content'),
            'created_at': datetime.now()
            }
    user_id = users.insert_one(user).inserted_id
    return redirect(url_for('users_show', user_id=user_id))


@app.route('/users/<user_id>/edit')
def users_edit(user_id):
    """Show the edit form for a user profile."""
    user = users.find_one({'_id': ObjectId(user_id)})
    return render_template('users_edit.html', user=user,
                           title='Edit User Profile')


@app.route('/users/<user_id>', methods=['POST'])
def users_update(user_id):
    """Submit an edited user profile."""
    updated_user = {
        'bio': request.form.get('content')
    }
    users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': updated_user})
    return redirect(url_for('users_show', user_id=user_id))


@app.route('/users/<user_id>')
def users_show(user_id):
    """Show a single user page."""
    user = users.find_one({'_id': ObjectId(user_id)})
    user_ranchos = ranchos.find({'user_id': ObjectId(user_id)})
    return render_template('users_show.html', user=user,
                           ranchos=user_ranchos)


@app.route('/users/<user_id>/delete', methods=['POST'])
def users_delete(user_id):
    """Delete one user."""
    users.delete_one({'_id': ObjectId(user_id)})
    return redirect(url_for('users_directory'))


@app.route('/listings_home')
def listings_home():
    """Return listings homepage."""
    return render_template('listings_index.html', listings=listings.find())


@app.route('/listings/new')
def listings_new():
    """Create a new listing."""
    return render_template('new_listing.html', listing={}, title='New Listing')


@app.route('/listings', methods=['POST'])
def listing_submit():
    """Submit a new listing."""
    # log in
    user = users.find_one({'username': request.form.get('username')})
    if user is None:
        return render_template('go_back.html')
    if user['password'] != request.form.get('password'):
        return render_template('go_back.html')
    listing = {'title': request.form.get('title'),
               'description': request.form.get('description'),
               'views': 0,
               'created_at': datetime.now(),
               'author': request.form.get('username'),
               'user_id': user['_id']
               }
    listing_id = listings.insert_one(listing).inserted_id
    return redirect(url_for('listings_show', listing_id=listing_id))


@app.route('/listings/<listing_id>')
def listings_show(listing_id):
    """Show a single listing."""
    listing = listings.find_one({'_id': ObjectId(listing_id)})
    listing_comments = comments.find({'listing_id': ObjectId(listing_id)})
    listing_author = users.find({'_id': listing['user_id']})

    updated_views = {
        'views': listing['views'] + 1
    }
    listings.update_one(
        {'_id': ObjectId(listing_id)},
        {'$set': updated_views})

    return render_template('listings_show.html', listing=listing,
                           comments=listing_comments, user=listing_author)


@app.route('/ranchos/<rancho_id>')
def ranchos_show(rancho_id):
    """Show a single Rancho."""
    rancho = ranchos.find_one({'_id': ObjectId(rancho_id)})
    listing_comments = comments.find({'rancho_id': ObjectId(rancho_id)})
    return render_template('ranchos_show.html', rancho=rancho,
                           comments=listing_comments)


@app.route('/listings/<listing_id>/edit')
def listings_edit(listing_id):
    """Show the edit form for a listing."""
    listing = listings.find_one({'_id': ObjectId(listing_id)})
    return render_template('listings_edit.html', listing=listing,
                           title='Edit Listing')


@app.route('/listings/<listing_id>', methods=['POST'])
def listings_update(listing_id):
    """Submit an edited listing."""
    # log in
    listing = listings.find_one({'_id': ObjectId(listing_id)})
    user = users.find_one({'_id': ObjectId(listing['user_id'])})
    if user is None:
        return render_template('go_back.html')
    if user['password'] != request.form.get('password'):
        return render_template('go_back.html')

    updated_listing = {
        'title': request.form.get('title'),
        'description': request.form.get('description')
    }
    listings.update_one(
        {'_id': ObjectId(listing_id)},
        {'$set': updated_listing})
    return redirect(url_for('listings_show', listing_id=listing_id))


@app.route('/ranchos/<rancho_id>/edit')
def ranchos_edit(rancho_id):
    """Show the edit form for a Rancho profile."""
    rancho = ranchos.find_one({'_id': ObjectId(rancho_id)})
    return render_template('ranchos_edit.html', rancho=rancho,
                           title='Edit Rancho Profile')


@app.route('/ranchos/<rancho_id>', methods=['POST'])
def ranchos_update(rancho_id):
    """Submit an edited rancho profile."""
    updated_prof = {
        'title': request.form.get('title'),
        'species': request.form.get('species'),
        'description': request.form.get('description')
    }
    ranchos.update_one(
        {'_id': ObjectId(rancho_id)},
        {'$set': updated_prof})
    return redirect(url_for('ranchos_show', rancho_id=rancho_id))


@app.route('/listings/<listing_id>/delete', methods=['POST'])
def listings_delete(listing_id):
    """Delete one listing."""
    # log in
    listing = listings.find_one({'_id': ObjectId(listing_id)})
    user = users.find_one({'_id': ObjectId(listing['user_id'])})
    if user is None:
        return render_template('go_back.html')
    if user['password'] != request.form.get('password'):
        return render_template('go_back.html')

    listings.delete_one({'_id': ObjectId(listing_id)})
    return redirect(url_for('listings_home'))


@app.route('/ranchos/<rancho_id>/release', methods=['POST'])
def ranchos_delete(rancho_id):
    """Release (delete) one Rancho."""
    ranchos.delete_one({'_id': ObjectId(rancho_id)})
    return redirect(url_for('listings_home'))


@app.route('/listings/comments', methods=['POST'])
def comments_new():
    """Submit a new comment."""
    comment = {
        'title': request.form.get('title'),
        'content': request.form.get('content'),
        'listing_id': ObjectId(request.form.get('listing_id'))
    }
    comments.insert_one(comment)
    return redirect(url_for('listings_show',
                            listing_id=request.form.get('listing_id')))


@app.route('/listings/comments/<comment_id>', methods=['POST'])
def comments_delete(comment_id):
    """Delete a comment."""
    comment = comments.find_one({'_id': ObjectId(comment_id)})
    comments.delete_one({'_id': ObjectId(comment_id)})
    return redirect(url_for('listings_show',
                            listing_id=comment.get('listing_id')))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
