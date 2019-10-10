"""RanchoStop is a site focusing on a modern rebranding of Tarantulas."""
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from datetime import datetime
from flask_session import Session
from functools import wraps

host = os.environ.get('MONGODB_URI', 'mongodb://127.0.0.1:27017/RanchoStop')
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


def login_required(f):
    """
    Require login to access a page.

    Adapted from:
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------HOME---------------------------
@app.route('/')
def home():
    """Return listings homepage."""
    current_user = None
    if 'user' in session:
        current_user = session['user']
    return render_template('home.html', current_user=current_user)


# ---------------------------LOGIN/OUT---------------------------
@app.route('/login')
def login():
    """Login from."""
    if 'user' in session:
        current_user = session['user']
        return render_template('logged_in.html', current_user=current_user)
    return render_template('login.html')


@app.route('/login/submit', methods=['POST'])
def login_submit():
    """Login submit."""
    current_user = None
    if 'user' in session:
        current_user = session['user']
    user = users.find_one({'username': request.form.get('username')})
    print(user['username'])
    if user is None:
        return redirect(url_for('login'))
    if user['password'] != request.form.get('password'):
        return redirect(url_for('login'))
    session['user'] = user
    return redirect(url_for('home', current_user=current_user))


@app.route('/logout')
def logout():
    """Remove user from session."""
    session.pop('user', None)
    return redirect(url_for('home'))


# ---------------------------USERS---------------------------
@app.route('/users/new')
def users_new():
    """Return a user creation page with starter Ranchos."""
    if 'user' in session:
        current_user = session['user']
        return render_template('logged_in.html', current_user=current_user)
    return render_template('new_user.html', user={}, title='New User')


@app.route('/users/directory')
def users_directory():
    """Return a directory of users."""
    current_user = None
    if 'user' in session:
        current_user = session['user']
    return render_template('users_directory.html', users=users.find(),
                           current_user=current_user)


@app.route('/users', methods=['POST'])
def users_submit():
    """Submit a new user."""
    if 'user' in session:
        current_user = session['user']
        return render_template('logged_in.html', current_user=current_user)
    if users.find_one({'username': request.form.get('username')}) is not None:
        return redirect(url_for('users_new'))
    user = {'username': request.form.get('username'),
            'password': request.form.get('password'),
            'bio': request.form.get('content'),
            'created_at': datetime.now()
            }
    user_id = users.insert_one(user).inserted_id
    return redirect(url_for('users_show', user_id=user_id))


@app.route('/users/<user_id>/edit')
@login_required
def users_edit(user_id):
    """Show the edit form for a user profile."""
    current_user = session['user']
    user = users.find_one({'_id': ObjectId(user_id)})
    if current_user['_id'] != user['_id']:
        print(current_user['_id'])
        print(user_id)
        return render_template('go_back.html', current_user=current_user)

    return render_template('users_edit.html', user=user,
                           title='Edit User Profile',
                           current_user=current_user)


@app.route('/users/<user_id>', methods=['POST'])
@login_required
def users_update(user_id):
    """Submit an edited user profile."""
    current_user = session['user']
    if current_user['_id'] != ObjectId(user_id):
        return render_template('go_back.html', current_user=current_user)

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
    current_user = None
    if 'user' in session:
        current_user = session['user']
    user = users.find_one({'_id': ObjectId(user_id)})
    user_ranchos = ranchos.find({'user_id': ObjectId(user_id)})
    return render_template('users_show.html', user=user,
                           ranchos=user_ranchos,
                           current_user=current_user)


@app.route('/users/<user_id>/delete', methods=['POST'])
@login_required
def users_delete(user_id):
    """Delete one user."""
    current_user = session['user']
    if current_user['_id'] != ObjectId(user_id):
        return render_template('go_back.html', current_user=current_user)
    users.delete_one({'_id': ObjectId(user_id)})
    session.pop('user', None)
    return redirect(url_for('users_directory'))


# ---------------------------LISTINGS---------------------------
@app.route('/listings_home')
def listings_home():
    """Return listings homepage."""
    current_user = None
    if 'user' in session:
        current_user = session['user']
    return render_template('listings_index.html', listings=listings.find(),
                           current_user=current_user)


@app.route('/listings/new')
@login_required
def listings_new():
    """Create a new listing."""
    current_user = session['user']
    return render_template('new_listing.html', listing={}, title='New Listing',
                           current_user=current_user)


@app.route('/listings', methods=['POST'])
@login_required
def listing_submit():
    """Submit a new listing."""
    current_user = session['user']
    listing = {'title': request.form.get('title'),
               'description': request.form.get('description'),
               'views': 0,
               'created_at': datetime.now(),
               'author': current_user['username'],
               'user_id': current_user['_id']
               }
    listing_id = listings.insert_one(listing).inserted_id
    return redirect(url_for('listings_show', listing_id=listing_id))


@app.route('/listings/<listing_id>')
def listings_show(listing_id):
    """Show a single listing."""
    current_user = None
    if 'user' in session:
        current_user = session['user']

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
                           comments=listing_comments, user=listing_author,
                           current_user=current_user)


@app.route('/listings/<listing_id>/edit')
@login_required
def listings_edit(listing_id):
    """Show the edit form for a listing."""
    current_user = session['user']
    listing = listings.find_one({'_id': ObjectId(listing_id)})
    if (current_user['_id'] != listing['user_id']):
        return render_template('go_back.html', current_user=current_user)
    return render_template('listings_edit.html', listing=listing,
                           title='Edit Listing', current_user=current_user)


@app.route('/listings/<listing_id>', methods=['POST'])
@login_required
def listings_update(listing_id):
    """Submit an edited listing."""
    current_user = session['user']
    listing = listings.find_one({'_id': ObjectId(listing_id)})
    if (current_user['_id'] != listing['user_id']):
        return render_template('go_back.html', current_user=current_user)

    updated_listing = {
        'title': request.form.get('title'),
        'description': request.form.get('description')
    }
    listings.update_one(
        {'_id': ObjectId(listing_id)},
        {'$set': updated_listing})
    return redirect(url_for('listings_show', listing_id=listing_id))


@app.route('/listings/<listing_id>/delete', methods=['POST'])
@login_required
def listings_delete(listing_id):
    """Delete one listing."""
    current_user = session['user']
    listing = listings.find_one({'_id': ObjectId(listing_id)})
    if (current_user['_id'] != listing['user_id']):
        return render_template('go_back.html', current_user=current_user)

    listings.delete_one({'_id': ObjectId(listing_id)})
    return redirect(url_for('listings_home'))


# ---------------------------RANCHOS---------------------------
@app.route('/ranchos/<rancho_id>')
def ranchos_show(rancho_id):
    """Show a single Rancho."""
    current_user = None
    if 'user' in session:
        current_user = session['user']
    rancho = ranchos.find_one({'_id': ObjectId(rancho_id)})
    listing_comments = comments.find({'rancho_id': ObjectId(rancho_id)})
    return render_template('ranchos_show.html', rancho=rancho,
                           comments=listing_comments,
                           current_user=current_user)


@app.route('/ranchos/<rancho_id>/edit')
def ranchos_edit(rancho_id):
    """Show the edit form for a Rancho profile."""
    current_user = None
    if 'user' in session:
        current_user = session['user']
    rancho = ranchos.find_one({'_id': ObjectId(rancho_id)})
    return render_template('ranchos_edit.html', rancho=rancho,
                           title='Edit Rancho Profile',
                           current_user=current_user)


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


@app.route('/ranchos/<rancho_id>/release', methods=['POST'])
def ranchos_delete(rancho_id):
    """Release (delete) one Rancho."""
    ranchos.delete_one({'_id': ObjectId(rancho_id)})
    return redirect(url_for('listings_home'))


# ---------------------------COMMENTS---------------------------
@app.route('/listings/comments', methods=['POST'])
@login_required
def comments_new():
    """Submit a new comment."""
    current_user = session['user']
    comment = {
        'title': request.form.get('title'),
        'content': request.form.get('content'),
        'listing_id': ObjectId(request.form.get('listing_id')),
        'author': current_user['username'],
        'user_id': current_user['_id']
    }
    comments.insert_one(comment)
    return redirect(url_for('listings_show',
                            listing_id=request.form.get('listing_id')))


@app.route('/listings/comments/<comment_id>', methods=['POST'])
@login_required
def comments_delete(comment_id):
    """Delete a comment."""
    current_user = session['user']
    comment = comments.find_one({'_id': ObjectId(comment_id)})
    if (current_user['_id'] != comment['user_id']):
        return render_template('go_back.html', current_user=current_user)

    comments.delete_one({'_id': ObjectId(comment_id)})
    return redirect(url_for('listings_show',
                            listing_id=comment.get('listing_id')))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
