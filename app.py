import datetime
import os
import random
import re

from flask import Flask, g, render_template, redirect, request, session, url_for
from flask_socketio import SocketIO, disconnect, emit, join_room, leave_room

# Users array
users = []

# Channels object
channels = {}

# Application initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
socketio = SocketIO(app)


# check for user
@app.before_request
def before_req():
   g.user = session.get('username')


# Log user in
@app.route('/', methods=['GET', 'POST'])
def index():
   if g.user:
      return render_template('index.html')
   
   return render_template('login.html')
   

@app.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == 'POST':
      username = request.form['username']

      if username == ' ' or username == '':
         return render_template('login.html')
             
      session['username'] = username

      session['color'] = "#%06x" % random.randint(0, 0xFFFFFF)

      users.append(username)

      return redirect(url_for('index'))
   
   return render_template('login.html')


@socketio.on('connect')
def connect():
   username = session['username']
   
   if username not in users:
      users.append(username)
   
   if not channels.get('global'):
      create_channel('global')

   emit('get channel name')


@socketio.on('logout')
def logout():
   session.pop('username', None)

   g.pop('user', None)
  

@socketio.on('receive channel name')
def receive_channel_name(data):
   session['current_channel'] = data['channel']

   if data['channel'] not in channels.keys():
      create_channel_on_event(data)

   join_channel(data)

   recreate_lists()


@socketio.on('new message')
def new_message(data):
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')

    message = {
      'username': session['username'].capitalize(),
      'color': session['color'],
      'timestamp': timestamp,
      'message': data['message']
      }
    
    add_message(session['current_channel'], message)
    
    recreate_lists()


@socketio.on('new channel')
def create_channel_on_event(data):
   channel = data['channel']

   create_channel(channel)

   recreate_lists()
    

@socketio.on('join channel')
def join_channel(data):
   newchannel = data['channel']

   if newchannel != session['current_channel']:
      username = session['username']

      session['current_channel'] = newchannel

      channels[channel]['users'].append(username)
   
      join_room(newchannel)
      
      message = message_from_server(f'User {username.capitalize()} joined {channel.capitalize()}')

      add_message(newchannel, message)
      
      recreate_lists()


@socketio.on('leave channel')
def leave_channel(data):
   username = session['username']

   channel = data['channel']

   message = message_from_server(f'User {username.capitalize()} left {channel.capitalize()} 😔')

   add_message(channel, message)

   leave_room(channel)


@socketio.on('disconnect')
def user_disconnected():
   channel = session.get('current_channel')

   if channel:
      leave_channel({'channel': channel})

   if session.get('username'):
      users.remove(session['username'])


# Add a message to a channel
def add_message(channel, message):
   
   message_capacity = 100

   channels[channel]['messages'].append(message)

   if len(channels[channel]['messages']) > message_capacity:
      channels[channel]['messages'] = channels[channel]['messages'][-message_capacity:]


# Create new channel
def create_channel(channel):
   if channel not in list(channels.keys()):
      channels[channel] = {'messages': [], 'users': []}

      return True   
   else:
      message = message_from_server(f'Uh oh! {channel} channel exists 😢 🤯')

      add_message(session['current_channel'], message)

      return False


# Keep lists upto date
def recreate_lists():
   channel_list = list(channels.keys())

   messages = channels[session['current_channel']]['messages']

   socketio.emit(
      'recreate lists', 
      {
      'channels': channel_list, 
      'messages': messages,
      'users': users
      })


def message_from_server(text):
   timestamp = datetime.datetime.now().strftime('%H:%M:%S')
   
   message = {
      'username': 'Server', 
      'timestamp': timestamp, 
      'message': text
      }
   
   return message


if __name__ == '__main__':
   socketio.run(app)