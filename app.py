"""RanchoStop is a site focusing on a modern rebranding of Tarantulas."""
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from datetime import datetime
from random import choice, randint
from functools import wraps
from bson import json_util
from bson.json_util import loads, dumps
import json
from lvl_calc import level_calc

host = os.environ.get('MONGODB_URI', 'mongodb://127.0.0.1:27017/RanchoStop')
client = MongoClient(host=f'{host}?retryWrites=false')
db = client.get_default_database()
users = db.users
ranchos = db.ranchos
listings = db.listings
comments = db.comments
hatcheries = db.hatcheries
broods = db.broods

app = Flask(__name__)
app.config['SECRET_KEY'] = 'THISISMYSECRETKEY'

# SESSION_TYPE = 'mongodb'
# app.config.from_object(__name__)
# Session(app)


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
    """Return homepage."""
    current_user = None
    if 'user' in session:
        current_user = session['user']
    return render_template('home.html', current_user=current_user)


@app.route('/home')
def home_page_redirect():
    """Redirect to homepage."""
    return redirect(url_for('home'))


# ---------------------------LOGIN/OUT---------------------------
@app.route('/login')
def login():
    """Login from."""
    if 'user' in session:
        current_user = session['user']
        return render_template('users/logged_in.html',
                               current_user=current_user)
    return render_template('users/login.html')


@app.route('/login/submit', methods=['POST'])
def login_submit():
    """Login submit."""
    current_user = None
    if 'user' in session:
        current_user = session['user']

    user = users.find_one({'username': request.form.get('username')})

    if user is None:
        return redirect(url_for('login'))
    if user['password'] != request.form.get('password'):
        return redirect(url_for('login'))

    data = {
        'username': request.form.get('username'),
        'user_id': str(user['_id'])
    }

    session['user'] = json.loads(json_util.dumps(data))

    current_user = session['user']
    return redirect(url_for('home', current_user=current_user))


@app.route('/logout')
def logout():
    """Remove user from session."""
    # session.pop('user', None)
    session.clear()
    return redirect(url_for('home'))


# ---------------------------USERS---------------------------
@app.route('/users/new')
def users_new():
    """Return a user creation page."""
    if 'user' in session:
        current_user = session['user']
        return render_template('users/logged_in.html',
                               current_user=current_user)
    return render_template('users/new_user.html', user={}, title='New User')


@app.route('/users/directory')
def users_directory():
    """Return a directory of users."""
    current_user = None
    if 'user' in session:
        current_user = session['user']

    return render_template('users/users_directory.html', users=users.find(),
                           current_user=current_user)


@app.route('/users', methods=['POST'])
def users_submit():
    """Submit a new user."""
    if 'user' in session:
        current_user = session['user']
        return render_template('users/logged_in.html',
                               current_user=current_user)

    if users.find_one({'username': request.form.get('username')}) is not None:
        return redirect(url_for('users_new'))

    user = {
        'username': request.form.get('username'),
        'password': request.form.get('password'),
        'bio': request.form.get('content'),
        'created_at': datetime.now(),
        'crikits': 200,
        'last_paid': datetime.now()
    }

    user_id = users.insert_one(user).inserted_id

    data = {
        'username': request.form.get('username'),
        'user_id': str(user_id)
    }

    session['user'] = json.loads(json_util.dumps(data))
    # print(user_id)
    # print(users.find_one({'username': request.form.get('username')})['_id'])
    # print(session['user']['user_id'])
    return redirect(url_for('users_show', user_id=user_id))


@app.route('/users/<user_id>/edit')
@login_required
def users_edit(user_id):
    """Show the edit form for a user profile."""
    current_user = session['user']

    user = users.find_one({'_id': ObjectId(user_id)})

    if ObjectId(current_user['user_id']) != user['_id']:
        return render_template('go_back.html', current_user=current_user)

    return render_template('users/users_edit.html', user=user,
                           title='Edit User Profile',
                           current_user=current_user)


@app.route('/daily_crikits')
@login_required
def daily_crikits():
    """Pay daily 25 crikits."""
    current_user = session['user']
    usid = current_user['user_id']

    a_user = users.find_one({'_id': ObjectId(current_user['user_id'])})
    timediff = datetime.now() - a_user['last_paid']
    if timediff.days >= 1:
        new_balance = a_user['crikits'] + 25
        users.update_one(
            {'_id': ObjectId(current_user['user_id'])},
            {'$set': {'crikits': new_balance, 'last_paid': datetime.now()}})
        return redirect(url_for('users_show', user_id=usid))

    error = {
        'error_message': "You've already claimed your daily reward in the last 24 hours.",
        'error_link': '/',
        'back_message': 'Back to home?'
    }
    return render_template('error_message.html', error=error, current_user=current_user)


@app.route('/users/<user_id>', methods=['POST'])
@login_required
def users_update(user_id):
    """Submit an edited user profile."""
    current_user = session['user']

    if ObjectId(current_user['user_id']) != ObjectId(user_id):
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
    # print(user['crikits'])

    user_ranchos = ranchos.find({'user_id': ObjectId(user_id)})
    return render_template('users/users_show.html', user=user,
                           ranchos=user_ranchos,
                           current_user=current_user)


@app.route('/users/<user_id>/delete', methods=['POST'])
@login_required
def users_delete(user_id):
    """Delete one user."""
    current_user = session['user']

    if ObjectId(current_user['user_id']) != ObjectId(user_id):
        return render_template('go_back.html', current_user=current_user)

    users.delete_one({'_id': ObjectId(user_id)})

    session.clear()  # Clear Session

    return redirect(url_for('users_directory'))


# ---------------------------LISTINGS---------------------------
@app.route('/listings_home')
def listings_home():
    """Return listings homepage."""
    current_user = None
    if 'user' in session:
        current_user = session['user']

    return render_template('/listings/listings_index.html',
                           listings=listings.find(), current_user=current_user)


@app.route('/listings/new')
@login_required
def listings_new():
    """Create a new listing."""
    current_user = session['user']

    return render_template('listings/new_listing.html',
                           listing={}, title='New Listing',
                           current_user=current_user)


@app.route('/listings', methods=['POST'])
@login_required
def listing_submit():
    """Submit a new listing."""
    current_user = session['user']
    listing = {
        'title': request.form.get('title'),
        'description': request.form.get('description'),
        'views': 0,
        'created_at': datetime.now(),
        'author': current_user['username'],
        'user_id': ObjectId(current_user['user_id'])
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

    return render_template('listings/listings_show.html', listing=listing,
                           comments=listing_comments, user=listing_author,
                           current_user=current_user)


@app.route('/listings/<listing_id>/edit')
@login_required
def listings_edit(listing_id):
    """Show the edit form for a listing."""
    current_user = session['user']
    listing = listings.find_one({'_id': ObjectId(listing_id)})

    if ObjectId(current_user['user_id']) != listing['user_id']:
        return render_template('go_back.html', current_user=current_user)

    return render_template('listings/listings_edit.html', listing=listing,
                           title='Edit Listing', current_user=current_user)


@app.route('/listings/<listing_id>', methods=['POST'])
@login_required
def listings_update(listing_id):
    """Submit an edited listing."""
    current_user = session['user']
    listing = listings.find_one({'_id': ObjectId(listing_id)})
    if ObjectId(current_user['user_id']) != listing['user_id']:
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
    if ObjectId(current_user['user_id']) != listing['user_id']:
        return render_template('go_back.html', current_user=current_user)

    listings.delete_one({'_id': ObjectId(listing_id)})
    return redirect(url_for('listings_home'))


# -------------------------RANCHOS-------------------------
@app.route('/ranchos/adoption_center')
@login_required
def adoption_center():
    """Show the adoption page with randomized ranchos."""
    current_user = session['user']
    rancho_species = ['Goliath Birdeater', 'Cobalt Blue']
    rancho_sex = ['Male', 'Female']
    ranchos_list = []

    for x in range(0, 9):
        rancho = {
            'species': choice(rancho_species),
            'sex': choice(rancho_sex),
            'stats': {
                'hardiness': randint(0, 100),
                'dexterity': randint(0, 100),
                'docility': randint(0, 100),
                'conformation': randint(0, 100),
            },
            'created_at': datetime.now()
        }
        ranchos_list.append(rancho)

    user_crikits = users.find_one({'username': current_user['username']})['crikits']

    return render_template('ranchos/adoption_center.html',
                           ranchos_list=ranchos_list,
                           current_user=current_user,
                           user_crikits=user_crikits)


@app.route('/ranchos/new', methods=['POST'])
@login_required
def ranchos_new():
    """Submit a new Rancho."""
    current_user = session['user']

    a_user = users.find_one({'_id': ObjectId(current_user['user_id'])})
    new_balance = a_user['crikits'] - 50
    if new_balance < 0:
        return render_template('go_back.html', current_user=current_user)
    users.update_one(
        {'_id': ObjectId(current_user['user_id'])},
        {'$set': {'crikits': new_balance}})

    stats = {
        'hardiness': request.form.get('hardiness'),
        'dexterity': request.form.get('dexterity'),
        'docility': request.form.get('docility'),
        'conformation': request.form.get('conformation')
    }
    needs = {
        'food': 100,
        'water': 100,
        'health': 100,
        'happiness': 100,
        'last_cared': datetime.now(),
        'cared_by': current_user['username'],
        'cared_by_id': ObjectId(current_user['user_id'])
    }
    rancho = {
        'name': 'New Rancho',
        'bio': request.form.get('sex') + ' ' + request.form.get('species'),
        'adopted_at': datetime.now(),
        'xp': 1000,
        'level': level_calc(1000),
        'stats': stats,
        'needs': needs,
        'species': request.form.get('species'),
        'sex': request.form.get('sex'),
        'owner': current_user['username'],
        'user_id': ObjectId(current_user['user_id'])
    }
    rancho_id = ranchos.insert_one(rancho).inserted_id

    return redirect(url_for('ranchos_edit', rancho_id=rancho_id))


@app.route('/ranchos/<rancho_id>')
def ranchos_show(rancho_id):
    """Show a single Rancho."""
    current_user = None
    if 'user' in session:
        current_user = session['user']
    rancho = ranchos.find_one({'_id': ObjectId(rancho_id)})

    if rancho is None:
        error = {
            'error_message': "That Rancho was not found. It may have been released.",
            'error_link': '/',
            'back_message': 'Back to home?'
        }
        return render_template('error_message.html', error=error,
                               current_user=current_user)

    # Update needs
    timediff = datetime.now() - rancho['needs']['last_cared']
    if timediff.days > 0:
        if timediff.days >= 4:
            # Been more than four days since last cared for
            new_needs = {
                'food': 0,
                'water': 0,
                'health': 0,
                'happiness': 0,
                'last_cared': rancho['needs']['last_cared'],
                'cared_by': rancho['needs']['cared_by'],
                'cared_by_id': rancho['needs']['cared_by_id']
            }

        elif timediff.days >= 3:
            # Been more than three days since last cared for

            new_needs = {
                'food': 25,
                'water': 0,
                'health': 50,
                'happiness': 0,
                'last_cared': rancho['needs']['last_cared'],
                'cared_by': rancho['needs']['cared_by'],
                'cared_by_id': rancho['needs']['cared_by_id']
            }

        elif timediff.days >= 2:
            # Been more than two days since last cared for
            new_needs = {
                'food': 50,
                'water': 0,
                'health': 100,
                'happiness': 50,
                'last_cared': rancho['needs']['last_cared'],
                'cared_by': rancho['needs']['cared_by'],
                'cared_by_id': rancho['needs']['cared_by_id']
            }

        elif timediff.days >= 1:
            # Been more than a day since last cared for
            new_needs = {
                'food': 75,
                'water': 50,
                'health': 100,
                'happiness': 75,
                'last_cared': rancho['needs']['last_cared'],
                'cared_by': rancho['needs']['cared_by'],
                'cared_by_id': rancho['needs']['cared_by_id']
            }
        ranchos.update_one(
            {'_id': ObjectId(rancho_id)},
            {'$set': {'needs': new_needs}}
            )

    return render_template('ranchos/ranchos_show.html',
                           rancho=ranchos.find_one({'_id': ObjectId(rancho_id)}),
                           broods=broods.find({'$or': [{'mother_id': ObjectId(rancho_id)}, {'father_id': ObjectId(rancho_id)}]}),
                           current_user=current_user)


@app.route('/ranchos/<rancho_id>/care')
@login_required
def ranchos_care(rancho_id):
    """Care for a Rancho."""
    current_user = session['user']
    rancho = ranchos.find_one({'_id': ObjectId(rancho_id)})

    timediff = datetime.now() - rancho['needs']['last_cared']
    if timediff.days >= 1:
        # Been more than a day since last cared for
        new_health = rancho['needs']['health'] + 50
        if new_health > 100:
            new_health = 100

        new_needs = {
            'food': 100,
            'water': 100,
            'health': new_health,
            'happiness': 100,
            'last_cared': datetime.now(),
            'cared_by': current_user['username'],
            'cared_by_id': ObjectId(current_user['user_id'])
        }

        new_xp = rancho['xp'] + 250
        ranchos.update_one(
            {'_id': ObjectId(rancho_id)},
            {'$set': {
                'needs': new_needs,
                'xp': new_xp,
                'level': level_calc(new_xp)
                }}
            )
    # Can care for other people's Ranchos
    # if ObjectId(current_user['user_id']) != rancho['user_id']:
    #     return render_template('go_back.html', current_user=current_user)

    return redirect(url_for('ranchos_show', rancho_id=rancho_id))


@app.route('/ranchos/<rancho_id>/edit')
@login_required
def ranchos_edit(rancho_id):
    """Show the edit form for a Rancho profile."""
    current_user = session['user']
    rancho = ranchos.find_one({'_id': ObjectId(rancho_id)})

    if ObjectId(current_user['user_id']) != rancho['user_id']:
        return render_template('go_back.html', current_user=current_user)

    return render_template('ranchos/ranchos_edit.html', rancho=rancho,
                           title='Edit Rancho Profile',
                           current_user=current_user)


@app.route('/ranchos/<rancho_id>', methods=['POST'])
@login_required
def ranchos_update(rancho_id):
    """Submit an edited rancho profile."""
    current_user = session['user']
    rancho = ranchos.find_one({'_id': ObjectId(rancho_id)})
    if ObjectId(current_user['user_id']) != rancho['user_id']:
        return render_template('go_back.html', current_user=current_user)

    updated_prof = {
        'name': request.form.get('rancho_name'),
        'bio': request.form.get('description')
    }
    ranchos.update_one(
        {'_id': ObjectId(rancho_id)},
        {'$set': updated_prof})

    # update rancho dict
    rancho = ranchos.find_one({'_id': ObjectId(rancho_id)})

    # update broods
    for brood in broods.find({'mother_id': rancho['_id']}):
        broods.update_one(
            {'_id': ObjectId(brood['_id'])},
            {'$set': {'mother_name': rancho['name']}})
    for brood in broods.find({'father_id': rancho['_id']}):
        broods.update_one(
            {'_id': ObjectId(brood['_id'])},
            {'$set': {'father_name': rancho['name']}})

    # update ancestry
    for other_rancho in ranchos.find({'ancestry.mother_id': rancho['_id']}):
        ranchos.update_one(
            {'_id': ObjectId(other_rancho['_id'])},
            {'$set': {'ancestry.mother_name': rancho['name']}})
    for other_rancho in ranchos.find({'ancestry.father_id': rancho['_id']}):
        ranchos.update_one(
            {'_id': ObjectId(other_rancho['_id'])},
            {'$set': {'ancestry.father_name': rancho['name']}})

    # update hatchery
    for hatchery in hatcheries.find({'mother_id': rancho['_id']}):
        hatcheries.update_one(
            {'_id': ObjectId(hatchery['_id'])},
            {'$set': {'mother_name': rancho['name']}})
    for hatchery in hatcheries.find({'father_id': rancho['_id']}):
        hatcheries.update_one(
            {'_id': ObjectId(hatchery['_id'])},
            {'$set': {'father_name': rancho['name']}})

    return redirect(url_for('ranchos_show', rancho_id=rancho_id))


@app.route('/ranchos/<rancho_id>/release', methods=['POST'])
@login_required
def ranchos_delete(rancho_id):
    """Release (delete) one Rancho."""
    current_user = session['user']
    rancho = ranchos.find_one({'_id': ObjectId(rancho_id)})

    # correct owner
    if ObjectId(current_user['user_id']) != rancho['user_id']:
        return render_template('go_back.html', current_user=current_user)

    # not currenly breeding
    if hatcheries.find(
        {'$or': [
            {'mother_id': ObjectId(rancho_id)},
            {'father_id': ObjectId(rancho_id)}
            ]}
            ).count() > 0:
        error = {
                'error_message': "That Rancho cannot be released because it is currently breeding.",
                'error_link': f'/ranchos/{ rancho_id }',
                'back_message': 'Back to Rancho?'
            }
        return render_template('error_message.html', error=error,
                               current_user=current_user)

    ranchos.delete_one({'_id': ObjectId(rancho_id)})

    a_user = users.find_one({'_id': ObjectId(current_user['user_id'])})
    new_balance = a_user['crikits'] + 25
    users.update_one(
        {'_id': ObjectId(current_user['user_id'])},
        {'$set': {'crikits': new_balance}})

    return redirect(url_for('users_show',
                            user_id=rancho.get('user_id')))


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
        'user_id': ObjectId(current_user['user_id'])
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

    if ObjectId(current_user['user_id']) != comment['user_id']:
        return render_template('go_back.html', current_user=current_user)

    comments.delete_one({'_id': ObjectId(comment_id)})
    return redirect(url_for('listings_show',
                            listing_id=comment.get('listing_id')))


# ---------------------------HATCHERIES---------------------------
@app.route('/hatcheries/new')
@login_required
def hatcheries_new():
    """Return a hatchery creation page."""
    current_user = session['user']
    return render_template('hatcheries/new_hatchery.html',
                           current_user=current_user)


@app.route('/hatcheries/my_hatcheries')
@login_required
def my_hatcheries():
    """Return a list of hatcheries extant broods belonging to the user."""
    current_user = session['user']

    for rancho in ranchos.find({'user_id': current_user['user_id']}):
        print(rancho['name'])

    return render_template('hatcheries/my_hatcheries.html',
                           hatcheries=hatcheries.find({
                               'user_id': ObjectId(current_user['user_id'])
                               }),
                           broods=broods.find({
                               'user_id': ObjectId(current_user['user_id'])
                               }),
                           f_ranchos=ranchos.find({
                               'user_id': ObjectId(current_user['user_id']),
                               'sex': 'Female'
                           }),
                           m_ranchos=ranchos.find({
                               'user_id': ObjectId(current_user['user_id']),
                               'sex': 'Male'
                           }),
                           current_user=current_user)


@app.route('/hatcheries', methods=['POST'])
@login_required
def hatcheries_submit():
    """Submit a new hatchery pairing."""
    current_user = session['user']
    a_user = users.find_one({'_id': ObjectId(current_user['user_id'])})

    mother = ranchos.find_one({'_id': ObjectId(request.form.get('mother'))})
    father = ranchos.find_one({'_id': ObjectId(request.form.get('father'))})

    if not check_compatible(mother, father):
        error = {
            'error_message': "These Ranchos are incompatible.",
            'error_link': f'/hatcheries/my_hatcheries',
            'back_message': 'Back to hatchery?'
        }
        return render_template('error_message.html', error=error,
                               current_user=current_user)

    hatchery = {
        'mother_name': mother['name'],
        'mother_id': mother['_id'],
        'father_name': father['name'],
        'father_id': father['_id'],
        'created_at': datetime.now(),
        'owner': a_user['username'],
        'user_id': a_user['_id']
    }

    hatchery_id = hatcheries.insert_one(hatchery).inserted_id

    return redirect(url_for('hatcheries_show', hatchery_id=hatchery_id))


@app.route('/hatcheries/<hatchery_id>')
def hatcheries_show(hatchery_id):
    """Show a single hatchery page."""
    current_user = None
    if 'user' in session:
        current_user = session['user']

    hatchery = hatcheries.find_one({'_id': ObjectId(hatchery_id)})
    mother = ranchos.find_one({'_id': ObjectId(hatchery['mother_id'])})
    father = ranchos.find_one({'_id': ObjectId(hatchery['father_id'])})

    ready_to_hatch = False
    timediff = datetime.now() - hatchery['created_at']
    if timediff.days >= 0:
        ready_to_hatch = True

    return render_template('hatcheries/hatcheries_show.html',
                           hatchery=hatchery,
                           mother=mother,
                           father=father,
                           ready=ready_to_hatch,
                           current_user=current_user)


@app.route('/hatcheries/<hatchery_id>/hatch', methods=['POST'])
@login_required
def hatchery_hatch(hatchery_id):
    """Hatch a brood and move record of the pairing to brood db."""
    current_user = session['user']
    hatchery = hatcheries.find_one({'_id': ObjectId(hatchery_id)})
    mother = ranchos.find_one({'_id': ObjectId(hatchery['mother_id'])})
    father = ranchos.find_one({'_id': ObjectId(hatchery['father_id'])})

    if ObjectId(current_user['user_id']) != ObjectId(hatchery['user_id']):
        error = {
            'error_message': "You don't own these Ranchos!",
            'error_link': f'/hatcheries/{hatchery_id}',
            'back_message': 'Back to hatchery?'
        }
        return render_template('error_message.html', error=error,
                               current_user=current_user)

    timediff = datetime.now() - hatchery['created_at']
    if timediff.days < 0:
        error = {
            'error_message': "This brood is not ready to hatch.",
            'error_link': f'/hatcheries/{hatchery_id}',
            'back_message': 'Back to hatchery?'
        }
        return render_template('error_message.html', error=error,
                               current_user=current_user)

    hatchling_ids = generate_hatchlings(mother, father)
    brood = {
        'mother_name': hatchery['mother_name'],
        'mother_id': hatchery['mother_id'],
        'father_name': hatchery['father_name'],
        'father_id': hatchery['father_id'],
        'breeder': hatchery['owner'],
        'user_id': hatchery['user_id'],
        'species': mother['species'],
        'hatched_at': datetime.now()}
    brood_id = broods.insert_one(brood).inserted_id

    for hatchling_id in hatchling_ids:
        ranchos.update_one(
            {'_id': ObjectId(hatchling_id)},
            {'$set': {'hatched_at': brood['hatched_at'],
                      'brood_id': brood_id}})

    hatcheries.delete_one({'_id': ObjectId(hatchery_id)})

    return redirect(url_for('broods_show',
                            brood_id=brood_id))


def check_compatible(mother, father):
    """Return true if the pairing is compatible."""
    # father is male and mother is female
    if mother['sex'] == father['sex']:
        return False
    # different species
    if mother['species'] != father['species']:
        return False
    # related
    if 'ancestry' in mother.keys():
        if mother['ancestry']['father_id'] == father['_id']:
            return False
        if 'ancestry' in father.keys():
            if mother['ancestry']['mother_id'] == father['ancestry']['mother_id']:
                return False
            if mother['ancestry']['father_id'] == father['ancestry']['father_id']:
                return False
    if 'ancestry' in father.keys():
        if father['ancestry']['mother_id'] == mother['_id']:
            return False
    # already breeding
    if hatcheries.find({'mother_id': mother['_id']}).count() > 0:
        return False
    if hatcheries.find({'father_id': father['_id']}).count() > 0:
        return False
    # both owned by current_user
    current_user = session['user']
    if mother['user_id'] != father['user_id']:
        return False
    if str(mother['user_id']) != str(current_user['user_id']):
        return False
    # level 3+
    if int(mother['level']) < 3:
        return False
    if int(father['level']) < 3:
        return False
    # full health
    if int(mother['needs']['health']) < 100:
        return False
    return True




def generate_hatchlings(mother, father):
    """Return list of new rancho hatchlings based on parents."""
    egg_count = randint(6, 10)  # 6-10 hatchlings per brood
    species = mother['species']  # parents should be same species
    rancho_sexes = ['Male', 'Female']  # pick random from this
    hatchlings = []  # list will contain the brood's hatchlings

    for count in range(1, egg_count):
        # Stat generation: between parents' stats, +/-20, 0<= stat<= 100
        hardiness = randint(
            min(
                int(mother['stats']['hardiness']),
                int(father['stats']['hardiness'])
            ) - 20,
            max(
                int(mother['stats']['hardiness']),
                int(father['stats']['hardiness'])
            ) + 20
        )
        if hardiness > 100:
            hardiness = 100
        elif hardiness < 0:
            hardiness = 0

        dexterity = randint(
            min(
                int(mother['stats']['dexterity']),
                int(father['stats']['dexterity'])
            ) - 20,
            max(
                int(mother['stats']['dexterity']),
                int(father['stats']['dexterity'])
            ) + 20
        )
        if dexterity > 100:
            dexterity = 100
        elif dexterity < 0:
            dexterity = 0

        docility = randint(
            min(
                int(mother['stats']['docility']),
                int(father['stats']['docility'])
            ) - 20,
            max(
                int(mother['stats']['docility']),
                int(father['stats']['docility'])
            ) + 20
        )
        if docility > 100:
            docility = 100
        elif docility < 0:
            docility = 0

        conformation = randint(
            min(
                int(mother['stats']['conformation']),
                int(father['stats']['conformation'])
            ) - 20,
            max(
                int(mother['stats']['conformation']),
                int(father['stats']['conformation'])
            ) + 20
        )
        if conformation > 100:
            conformation = 100
        elif conformation < 0:
            conformation = 0

        stats = {
            'hardiness': str(hardiness),
            'dexterity': str(dexterity),
            'docility': str(docility),
            'conformation': str(conformation)
        }
        needs = {
            'food': 100,
            'water': 100,
            'health': 100,
            'happiness': 100,
            'last_cared': datetime.now(),
            'cared_by': mother['owner'],
            'cared_by_id': ObjectId(mother['user_id'])
        }
        ancestry = {
            'mother_name': mother['name'],
            'mother_id': mother['_id'],
            'father_name': father['name'],
            'father_id': father['_id']
        }
        rancho_sex = choice(rancho_sexes)
        rancho = {
            'name': 'Hatchling Rancho',
            'bio': rancho_sex + ' ' + species,
            'xp': 0,
            'level': 0,
            'stats': stats,
            'needs': needs,
            'ancestry': ancestry,
            'species': species,
            'sex': rancho_sex,
            'owner': mother['owner'],
            'user_id': ObjectId(mother['user_id'])
        }
        rancho_id = ranchos.insert_one(rancho).inserted_id
        hatchlings.append(rancho_id)
    return hatchlings


# ---------------------------BROODS---------------------------
@app.route('/broods/<brood_id>')
def broods_show(brood_id):
    """Show a single brood page."""
    current_user = None
    if 'user' in session:
        current_user = session['user']

    brood = broods.find_one({'_id': ObjectId(brood_id)})
    mother = ranchos.find_one({'_id': ObjectId(brood['mother_id'])})
    father = ranchos.find_one({'_id': ObjectId(brood['father_id'])})

    return render_template('broods/broods_show.html',
                           brood=brood,
                           mother=mother,
                           father=father,
                           hatchlings=ranchos.find({'brood_id': ObjectId(brood_id)}),
                           current_user=current_user)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
