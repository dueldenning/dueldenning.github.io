import os
import logging

import flask
from flask import Flask, render_template, redirect, request, session, url_for
import flask_socketio
from flask_socketio import SocketIO

from rooms import RoomsController
from tasks import Tasks

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']
socketio = SocketIO(app, path='/io')

open_rooms = RoomsController()
tasks = Tasks('./tasks')

# ----------------------------------------------------------
@app.route('/', methods=['GET'])
def on_get_index():
    session.permanent = True
    username = request.args.get('username')
    if username is not None:
        app.logger.debug('Setting username from args: ' + username)
        session['username'] = username

    if 'username' not in session:
        username = 'New User'
        app.logger.debug('Setting username to default: ' + username)
        session['username'] = username

    return render_template(
        "index.html", username=session['username'], rooms=open_rooms.open_room_names(), tasks=tasks.task_names())

# ----------------------------------------------------------
@app.route("/task/<string:task_name>/id/<int:room_id>", methods=["GET"])
def on_get_task(task_name, room_id):
    if 'username' not in session:
        return redirect(url_for('on_get_index'))

    if not tasks.exists(task_name):
        flask.abort(404)

    return render_template("task.html", username=session['username'], task=task)

# ----------------------------------------------------------
@socketio.on('connect')
def on_connect():
    app.logger.debug('On Connect:' + str(request))

@socketio.on('disconnect')
def on_disconnect():
    app.logger.debug('On Disconnect: ' + str(request))

    task_name = request.args['task_name']
    room_id = request.args['room_id']
    room_name = "{task_name}/{room_id}".format(task_name=task_name, room_id=room_id)
    username = session['username']

    metadata = open_rooms.get_metadata(room_name)

    state = metadata['state']
    state['chat'].append({
        'username': 'Server',
        'message': '{} has left the room.'.format(username),
        })

    open_rooms.emit_in_room(room_name, 'state change', {'new_state': state})
    open_rooms.leave_room(request.sid, room_name)

@socketio.on('join')
def on_join(message):
    app.logger.debug('On Join: ' + str(message))

    task_name = request.args['task_name']
    room_id = request.args['room_id']
    room_name = "{task_name}/{room_id}".format(task_name=task_name, room_id=room_id)
    username = session['username']

    room_metatdata = open_rooms.join_or_create(request.sid, room_name)

    if 'state' in room_metatdata:
        state = room_metatdata['state']
        assignments = state['assignments']
        if username in assignments:
            app.logger.warn('User already assigned. This should ever happen?')
        else:
            numb_briefs = len(state['task']['briefs'])
            num_current_assignments = len(assignments)
            assignments[username] = num_current_assignments % numb_briefs
    else:
        task = tasks.get(task_name)
        default_options = {option_name: option_values[0] for option_name, option_values in task['options'].items()}
        state = {
            'task': task,
            'options': default_options,
            'chat': [{
                'username': 'Server',
                'message': '{} room created.'.format(task_name),
            }],
            'assignments': {
                username: 0,
            },
        }
        room_metatdata['state'] = state
    state['chat'].append({
                'username': 'Server',
                'message': '{} has joined the room.'.format(username),
            })
    open_rooms.emit_in_room(room_name, 'state change', {'new_state': state})

@socketio.on('state change')
def on_relay_message(message):
    app.logger.debug('On State Change: ' + str(message))

    task_name = request.args['task_name']
    room_id = request.args['room_id']
    room_name = "{task_name}/{room_id}".format(task_name=task_name, room_id=room_id)
    username = session['username']

    new_state = message['new_state']
    
    open_rooms.get_metadata(room_name)['state'] = new_state
    open_rooms.emit_in_room(room_name, 'state change', {'new_state': new_state})


# ----------------------------------------------------------
if __name__ == "__main__":
    socketio.run(app)
