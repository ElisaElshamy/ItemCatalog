# Import necessary libraries and frameworks
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Genre, Games
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Video Game Catalog"

engine = create_engine('sqlite:///videogames.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Home pages - available to all users
@app.route('/')
@app.route('/gaming')
def showGames():
    user_id = 0
    user_pic = ''
    if 'user_id' in login_session:
        user_id = login_session['user_id']
        user_pic = login_session['picture']

    # Generates a random string as a anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
    login_session['state'] = state
    genres = session.query(Genre).order_by(asc(Genre.name))
    games = session.query(Games).order_by(desc(Games.id)).limit(5)
    return render_template('gaming.html', genres=genres, games=games, user_id = user_id, user_pic=user_pic, STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token - checks if the state string created in showLogin
    # matches the one from the get request
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
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
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
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
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


    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h4>Welcome, '
    output += login_session['username']
    output += '!</h4>'
    flash('You are logged in as %s' % login_session['username'])
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['user_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
        
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON API
@app.route('/gaming/<int:genre_id>/games/json')
def gamingJSON(genre_id):
    genre = session.query(Genre).filter_by(id=genre_id).one()
    games = session.query(Games).filter_by(
        genre_id=genre_id).all()

    return jsonify(VideoGames=[vg.serialize for vg in games])



# Authenticated users can add new genres
@app.route('/gaming/genre/new', methods=['GET', 'POST'])
def newGamingGenre():
    user_id = 0
    user_pic = ''
    if 'user_id' in login_session:
        user_id = login_session['user_id']
        user_pic = login_session['picture']

    if request.method == 'POST':
        newGenre = Genre(name=request.form['name'], creator_id=user_id)
        session.add(newGenre)
        flash('New Genre %s Successfully Added' % newGenre.name)
        session.commit()
        return redirect(url_for('showGames'))

    return render_template('new_genre.html', user_id = user_id, user_pic=user_pic)


# Authenticated users can edit a genre
@app.route('/gaming/genre/<int:genre_id>/edit', methods=['GET', 'POST'])
def editGamingGenre(genre_id):
    user_id = 0
    user_pic = ''
    if 'user_id' in login_session:
        user_id = login_session['user_id']
        user_pic = login_session['picture']

    editedGenre = session.query(
        Genre).filter_by(id=genre_id).one()

    if request.method == 'POST' and request.form['submit'] == 'Save':
        if request.form['name']:
            editedGenre.name = request.form['name']
            flash('Genre Successfully Edited %s' % editedGenre.name)
            return redirect(url_for('showGames'))
    elif request.method == 'POST' and request.form['submit'] == 'Cancel':
        return redirect(url_for('showGames'))

    return render_template('edit_genre.html', genre=editedGenre, user_id=user_id, user_pic=user_pic)


# Authenticated users can delete a genre
@app.route('/gaming/genre/<int:genre_id>/delete', methods=['GET', 'POST'])
def deleteGamingGenre(genre_id):
    user_id = 0
    user_pic = ''
    if 'user_id' in login_session:
        user_id = login_session['user_id']
        user_pic = login_session['picture']

    genreToDelete = session.query(
        Genre).filter_by(id=genre_id).one()

    if request.method == 'POST' and request.form['submit'] == 'Delete':
        session.delete(genreToDelete)
        flash('%s Successfully Deleted' % genreToDelete.name)
        session.commit()
        return redirect(url_for('showGames'))
    elif request.method == 'POST' and request.form['submit'] == 'Cancel':
        return redirect(url_for('showGames'))

    return render_template('delete_genre.html', genre=genreToDelete, user_id=user_id, user_pic=user_pic)


# Genre pages - available to all users
@app.route('/gaming/genre/<int:genre_id>')
@app.route('/gaming/genre/<int:genre_id>/games')
def showGamingGenre(genre_id):
    user_id = 0
    user_pic = ''
    if 'user_id' in login_session:
        user_id = login_session['user_id']
        user_pic = login_session['picture']
    genre = session.query(Genre).filter_by(id=genre_id).one()
    videoGames = session.query(Games).filter_by(genre_id=genre.id)

    return render_template(
        'genre.html', genre=genre, videoGames=videoGames, genre_id=genre_id, user_id=user_id, user_pic=user_pic)


# Authenticated users can add new game to a genre
@app.route('/gaming/<int:genre_id>/game/new', methods=['GET', 'POST'])
def newGenreGame(genre_id):
    user_id = 0
    user_pic = ''
    if 'user_id' in login_session:
        user_id = login_session['user_id']
        user_pic = login_session['picture']

    genre = session.query(Genre).filter_by(id=genre_id).one()

    if request.method == 'POST':
        newVideoGame = Games(title=request.form['title'], description=request.form[
            'description'], boxart=request.form['boxart'], genre_id=genre_id, creator_id = user_id)
        session.add(newVideoGame)
        session.commit()
        flash("Video Game Added!")
        return redirect(url_for('showGamingGenre', genre_id=genre_id))

    return render_template('new_game.html', genre=genre, user_id=user_id, user_pic=user_pic)


# Authenticated users can edit a game in a genre
@app.route('/gaming/<int:genre_id>/<int:game_id>/edit', methods=['GET', 'POST'])
def editGenreGame(genre_id, game_id):
    user_id = 0
    user_pic = ''
    if 'user_id' in login_session:
        user_id = login_session['user_id']
        user_pic = login_session['picture']

    editedGame = session.query(Games).filter_by(id=game_id).one()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    genres = session.query(Genre).order_by(asc(Genre.name))

    if request.method == 'POST' and request.form['submit'] == 'Save':
        if request.form['title']:
            editedGame.title = request.form['title']
        if request.form['description']:
            editedGame.description = request.form['description']
        if request.form['boxart']:
            editedGame.boxart = request.form['boxart']
        if request.form['genre']:
            editedGame.genre_id = request.form['genre']

        session.add(editedGame)
        session.commit()
        flash('Video Game Successfully Edited')
        return redirect(url_for('showGamingGenre', genre_id=genre_id))
    elif request.method == 'POST' and request.form['submit'] == 'Cancel':
        return redirect(url_for('showGamingGenre', genre_id=genre_id))
    
    return render_template('edit_game.html', genres=genres, genre=genre, game_id=game_id, videoGame=editedGame, user_id=user_id, user_pic=user_pic)


# Authenticated users can delete a game in a genre
@app.route('/gaming/<int:genre_id>/<int:game_id>/delete', methods=['GET', 'POST'])
def deleteGenreGame(genre_id, game_id):
    user_id = 0
    user_pic = ''
    if 'user_id' in login_session:
        user_id = login_session['user_id']
        user_pic = login_session['picture']

    genre = session.query(Genre).filter_by(id=genre_id).one()
    gameToDelete = session.query(Games).filter_by(id=game_id).one()

    if request.method == 'POST' and request.form['submit'] == 'Delete':
        session.delete(gameToDelete)
        session.commit()
        flash('Video Game Successfully Deleted')
        return redirect(url_for('showGamingGenre', genre_id=genre_id))
    elif request.method == 'POST' and request.form['submit'] == 'Cancel':
        return redirect(url_for('showGamingGenre', genre_id=genre_id))

    return render_template('delete_game.html', genre=genre, videoGame=gameToDelete, user_id=user_id, user_pic=user_pic)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
