from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app import socketio, db
from models import Room, Note
from datetime import datetime

@socketio.on('join_room')
def on_join_room(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data['room_id']
    room = Room.query.filter_by(room_id=room_id).first()
    
    if room and current_user in room.members:
        join_room(room_id)
        emit('user_joined', {
            'username': current_user.username,
            'user_id': current_user.id
        }, to=room_id)

@socketio.on('leave_room')
def on_leave_room(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data['room_id']
    leave_room(room_id)
    emit('user_left', {
        'username': current_user.username,
        'user_id': current_user.id
    }, to=room_id)

@socketio.on('timer_start')
def on_timer_start(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data['room_id']
    subtopic_id = data['subtopic_id']
    
    emit('timer_started', {
        'user_id': current_user.id,
        'username': current_user.username,
        'subtopic_id': subtopic_id
    }, to=room_id)

@socketio.on('timer_stop')
def on_timer_stop(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data['room_id']
    subtopic_id = data['subtopic_id']
    duration = data.get('duration', 0)
    
    emit('timer_stopped', {
        'user_id': current_user.id,
        'username': current_user.username,
        'subtopic_id': subtopic_id,
        'duration': duration
    }, to=room_id)

@socketio.on('add_note')
def on_add_note(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data['room_id']
    content = data['content'].strip()
    
    if not content:
        return
        
    room = Room.query.filter_by(room_id=room_id).first()
    
    if room and current_user in room.members:
        note = Note()
        note.content = content
        note.room_id = room.id
        note.author_id = current_user.id
        
        db.session.add(note)
        db.session.commit()
        
        emit('note_added', note.to_dict(), to=room_id)

@socketio.on('progress_update')
def on_progress_update(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data['room_id']
    subtopic_id = data['subtopic_id']
    status = data['status']
    
    emit('progress_updated', {
        'user_id': current_user.id,
        'username': current_user.username,
        'subtopic_id': subtopic_id,
        'status': status
    }, to=room_id)
