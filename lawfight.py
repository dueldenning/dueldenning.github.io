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
    task = tasks.get(task_name)

    return render_template("task.html", room_id=room_id, username=session['username'], task=task)

# ----------------------------------------------------------
@socketio.on('connect')
def on_connect():
    app.logger.debug('Connect:' + str(request))

@socketio.on('disconnect')
def on_disconnect():
    app.logger.debug('disconnect: ' + str(request))
    # TODO
    #open_rooms.emit_in_present_rooms(
    #    request.sid, 'chat', {'msg': 'Left to room', 'username': session['username']})
    open_rooms.leave_all_rooms(request.sid)

@socketio.on('join')
def on_join(message):
    app.logger.debug('message: ' + str(message))
    task_name = message['task_name']
    room_name = "{task_name}/{room_id}".format(task_name=task_name, room_id=message['room_id'])
    
    open_rooms.leave_all_rooms(request.sid)
    room_metatdata = open_rooms.join_or_create(request.sid, room_name)

    if 'state' in room_metatdata:
        state = room_metatdata['state']
    else:
        task = tasks.get(task_name)
        default_options = {option_name: option_values[0] for option_name, option_values in task.options.items()}
        state = {
            'options': default_options,
            'chat': [],
            'assignments': {username: 0, 'Jane': 1}, # TODO
        }
        room_metatdata['state'] = state
    open_rooms.emit_in_present_rooms(request.sid, 'state change', {'new_state': state})

@socketio.on('state change')
def on_relay_message(message):
    app.logger.debug('state change: ' + str(message))
    room_name = "{task_name}/{room_id}".format(task_name=message['task_name'], room_id=message['room_id'])
    new_state = message['new_state']
    
    open_rooms.get_metadata(room_name)['state'] = new_state
    open_rooms.emit_in_present_rooms(request.sid, 'state change', {'new_state': new_state})


# ----------------------------------------------------------
if __name__ == "__main__":
    socketio.run(app)
