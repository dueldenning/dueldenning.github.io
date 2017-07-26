import flask_socketio

class RoomsController(object):
    def __init__(self):
        super(RoomsController, self).__init__()
        self._rooms = {}

    def open_room_names(self):
        return [key for key in self._rooms.keys()]

    def join_or_create(self, sid, room_name):
        """ Joins a room, creating it if it did not exist.
        Args:
            sid: The clients SID.
            room_name: The rooms name.
        Returns:
            Dict: The rooms metatdata.
        """
        room = self._rooms.get(room_name)
        if room is None:
            room = RoomController(room_name)
            self._rooms[room_name] = room
        room.join(sid)
        return room.metatdata()

    def emit_in_present_rooms(self, sid, event, *args, **kwargs):
        for room in self._rooms.values():
            if room.is_present(sid):
                room.emit(event, *args, **kwargs)

    def leave_all_rooms(self, sid):
        keys_to_remove = []
        for room_name, room in self._rooms.items():
            room.leave(sid)
            if room.is_empty():
                room.destroy()
                keys_to_remove.append(room_name)
        for room_name in keys_to_remove:
            self._rooms.pop(room_name)

    def get_metadata(self, room_name):
        return self._rooms[room_name].metatdata()


class RoomController(object):
    def __init__(self, room_name):
        super(RoomController, self).__init__()
        self._room_name = room_name
        self._sids = set()
        self._metatdata = {}

    def join(self, sid):
        if self.is_present(sid):
            return
        self._sids.add(sid)
        flask_socketio.join_room(self._room_name, sid=sid)

    def leave(self, sid):
        if not self.is_present(sid):
            return
        flask_socketio.leave_room(self._room_name, sid=sid)
        self._sids.remove(sid)

    def is_present(self, sid):
        return sid in self._sids

    def is_empty(self):
        return len(self._sids) == 0

    def destroy(self):
        flask_socketio.close_room(self._room_name)

    def emit(self, event, *args, **kwargs):
        kwargs['room'] = self._room_name
        flask_socketio.emit(event, *args, **kwargs) # room=self._room_name

    def metatdata(self):
        return self._metatdata
