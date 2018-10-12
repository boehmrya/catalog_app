from flask import Flask, render_template, make_response
from flask import request, redirect, jsonify, url_for, flash
from flask import session as login_session
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, User, Item
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from datetime import datetime
import httplib2
import json
import requests
import random
import string


app = Flask(__name__)


# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db?check_same_thread=False')
Base.metadata.bind = engine


# start db session
DBSession = sessionmaker(bind=engine)
session = DBSession()


# client id for oauth2
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


APPLICATION_NAME = "Catalog Application"


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# facebook login
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?' \
        'grant_type=fb_exchange_token&client_id=%s&client_secret' \
        '=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
    Due to the formatting for the result from the server token
    exchange we have to split the token first on commas and select
    the first index which gives us the key : value for the server
    access token then we split it on colons to pull out the actual
    token value and replace the remaining quotes with nothing so that
    it can be used directly in the graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?' \
        'access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?' \
        'access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px;' \
        'height: 300px;' \
        'border-radius: 150px;' \
        '-webkit-border-radius:' \
        ' 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


# facebook logout
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions' \
        '?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return redirect(url_for('showHome'))


# google plus login
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is '
                                            'already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px;' \
        'height: 300px;' \
        'border-radius: 150px;' \
        '-webkit-border-radius: 150px;' \
        '-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# google plus logout
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user '
                                            'not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/' \
        'revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showHome'))
    else:
        response = make_response(json.dumps('Failed to revoke token'
                                            'for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Show home page
@app.route('/')
def showHome():
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).join(Item.category)
    return render_template('home.html', categories=categories, items=items)


# Show category page
@app.route('/catalog/<category_name>/items')
def showCategory(category_name):
    main_category = session.query(Category).filter_by(name=category_name).one()
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).filter_by(category_id=main_category.id)
    items = items.order_by(asc(Item.name)).all()
    return render_template('category.html',
                           main_category=main_category,
                           categories=categories,
                           items=items)


# Show item page
@app.route('/catalog/<category_name>/<item_name>')
def showItem(category_name, item_name):
    item = session.query(Item).filter_by(name=item_name).one()
    creator = getUserInfo(item.author_id)
    return render_template('item.html', item=item, creator=creator)


# Create a new item
@app.route('/catalog/item/new/', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('login')
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       category_id=request.form['category'],
                       author_id=login_session['user_id'],
                       created=datetime.now(),
                       updated=datetime.now())
        session.add(newItem)
        flash('New Item %s Successfully Created' % newItem.name)
        session.commit()
        return redirect(url_for('showHome'))
    else:
        categories = session.query(Category).order_by(asc(Category.name)).all()
        return render_template('newItem.html', categories=categories)


# Edit an item
@app.route('/catalog/<item_name>/edit/', methods=['GET', 'POST'])
def editItem(item_name):
    editedItem = session.query(Item).filter_by(name=item_name).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
            editedItem.category_id = request.form['category']
            editedItem.description = request.form['description']
            editedItem.updated = datetime.now()
            flash('Item %s Successfully Edited' % editedItem.name)
            return redirect(url_for('showItem',
                                    category_name=editedItem.category.name,
                                    item_name=editedItem.name))
    else:
        if 'username' not in login_session:
            return redirect('login')
        else:
            categories = session.query(Category)
            categories = categories.order_by(asc(Category.name)).all()
            cat = session.query(Category)
            selected_category = cat.filter_by(id=editedItem.category_id).one()
            return render_template('editItem.html',
                                   item=editedItem,
                                   categories=categories,
                                   selected_category=selected_category)


# Delete an item
@app.route('/catalog/<item_name>/delete/', methods=['GET', 'POST'])
def deleteItem(item_name):
    itemToDelete = session.query(Item).filter_by(name=item_name).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        flash('%s Successfully Deleted' % itemToDelete.name)
        session.commit()
        return redirect(url_for('showHome'))
    else:
        return render_template('deleteItem.html', item=itemToDelete)


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# JSON API endpoint to view all content
@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(Category).order_by(asc(Category.name))
    newCategories = {}
    newCategories['Category'] = []
    for category in categories:
        newCategory = {}
        newCategory['id'] = category.id
        newCategory['name'] = category.name
        items = session.query(Item).filter_by(category_id=category.id)
        newItems = [i.serialize for i in items]
        newCategory['items'] = newItems

        # add serialized version of category to new list
        newCategories['Category'].append(newCategory)
    return jsonify(newCategories)


# JSON API endpoint to view all items of a given category
@app.route('/catalog/<category_name>/items/JSON')
def categoryItemsJSON(category_name):
    main_category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item)
    items = items.filter_by(category_id=main_category.id)
    items = items.order_by(asc(Item.name)).all()
    return jsonify(Items=[i.serialize for i in items])


# JSON API endpoint to view all content of a given item
@app.route('/catalog/<category_name>/<item_name>/JSON')
def itemJSON(category_name, item_name):
    item = session.query(Item).filter_by(name=item_name).one()
    return jsonify(Item=item.serialize)


# run app
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
