import os
import datetime
import random
import re

from database import db_session
from werkzeug import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from flask import Flask, render_template, request, session, redirect, url_for

# Local modules
from models import User, Channel, Message

# Initialize application
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY')

@app.before_request
def before_request():
    session.permanent = True

    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

# DB connection
if not os.environ.get('DATABASE_URL'):
    raise RuntimeError("DATABASE_URL not set")

# SocketIO
socketio = SocketIO(app)

# Retrieve channels
channels = []
for channel in db_session.query(Channel).all():
    channels.append(channel.channel)

@app.route("/")
def index():
    # If no user
    if not session.get("username"):
        return redirect(url_for("signup"))

    # If user
    else:
        # If repeated user
        if session.get('current_channel'):
            return redirect(url_for("display_channel", channel=session.get('current_channel')))

        # Otherwise global channel
        else:
            return redirect(url_for("display_channel", channel=channels[0]))

# Chatrooms
@app.route("/<channel>", methods=['GET', 'POST'])
def display_channel(channel):
    # GET request
    if request.method == 'GET':
        if not session.get('userid'):
            return redirect(url_for("index"))

        # Get mesages in the current channel
        messages = db_session.query(Message).filter_by(channel=channel).all()

        session['current_channel'] = channel
        
        return render_template("main.html", messages=messages, channels=channels)

    # POST request
    else:
        error = None
        
        # Get users channel name input
        channel_name = request.form.get('channel-name')

        if ' ' in channel_name:
            error = ' Please provide a channel name'
            return render_template('main.html', error=error, channels=channels)

        # Store channel
        try:
            new_channel = Channel(channel=channel_name, created_by=session.get('userid'))

            db_session.add(new_channel)

            db_session.commit()

            channels.append(channel_name)

            # Direct user to chatroom
            return redirect(url_for("display_channel", channel=channel_name))

        # Channel exists
        except:
            error = 'Oh uh, this channel exists'
            return render_template('main.html', error=error, channels=channels)

@app.route("/login", methods=["GET", "POST"])
def login():
    # GET request
    if request.method == 'GET':
        if not session.get("username"):
            return render_template("login.html")

        else:
            return redirect(url_for("index"))
        
    # POST request
    else:
        error = None

        # Login details
        username = request.form.get('username')

        password = request.form.get('password')

        # Login authentication
        if username == '':
            error = 'Please enter a username'
            return render_template('login.html', error=error)

        if password == '':
            error = ' Please enter a password'
            return render_template('login.html', error=error)

        try:
            user = db_session.query(User).filter_by(username=username).one()
            
        except:
            error = 'Oh uh, this username is taken'
            return render_template('login.html', error=error)

        if check_password_hash(user.hash, password) == False:
            error = 'Oh uh, incorrect password'
            return render_template('login.html', error=error)

        else:
            session['username'] = username

            session['userid'] = db_session.query(User).filter_by(username=username).one().id

            session['color'] = "#%06x" % random.randint(0, 0xFFFFFF)
            
            return redirect(url_for('index'))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None

    # GET request
    if request.method == 'GET':
        if not session.get("username"):
            return render_template("signup.html")

        else:
            return redirect(url_for("index"))

    # POST request
    else:
        username = request.form.get('username')

        password = request.form.get('password')

        confirm_password = request.form.get('confirm-password')

        # Validate username
        if not re.search(r'^[A-Za-z0-9_-]+$', username):
            error = 'Oh uh, username must only contains: alphabets, numbers, underscore and/or hyphen'
            return render_template('signup.html', error = error)

        if db_session.query(User).filter_by(username = username).all() == []:
            if password == confirm_password:
                new_user = User(username = username, hash = generate_password_hash(password))

                session['username'] = username

                db_session.add(new_user)

                db_session.commit()

                session['userid'] = db_session.query(User).filter_by(username = username).one().id
                
                session['username'] = username

                return redirect(url_for("index"))

            else:
                error = 'Oh uh, passwords do not match'

                return render_template('signup.html', error = error)
        else:
            error = 'Oh uh, this username is taken'

            return render_template('signup.html', error = error)

@app.route("/logout")
def logout():
    session.pop('username')

    session.pop('userid')

    return redirect(url_for('login'))

# Disconnection
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

# SocketIO
@socketio.on('submit post')
def post(data):
    new_post = Message(user_id=session.get('userid'), channel=data['room'], message=data['message'])

    db_session.add(new_post)

    db_session.commit()

    emit('announce post', data, room=data['room'], broadcast=True)

# Joining a chatroom
@socketio.on('join')
def on_join(data):

    room = data['room']

    join_room(room)

    data['message'] = ': joined the room'

    emit('join room', data, room=room, broadcast=True)

# Leaving a chatroom
@socketio.on('leave')
def on_leave(data):

    room = data['room']

    data['message'] = ': has left the room'

    emit('leave room', data, room=room, broadcast=True)

    leave_room(room)

    # session['color'] = "#%06x" % random.randint(0, 0xFFFFFF)
    # timestamp = datetime.datetime.now().strftime('%H:%M:%S')