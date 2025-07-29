from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
import os
import uuid
from werkzeug.utils import secure_filename
from io import BytesIO
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, date
from app import app, db
from models import User, Room, Topic, Subtopic, UserProgress, StudySession, Note, FileNote

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User()
        user.username = username
        user.email = email
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    created_rooms = current_user.created_rooms.all()
    joined_rooms = [room for room in current_user.joined_rooms if room not in created_rooms]
    
    return render_template('dashboard.html', 
                         created_rooms=created_rooms, 
                         joined_rooms=joined_rooms)

@app.route("/create_room", methods=["GET", "POST"])
@login_required  # This ensures only logged-in users can access
def create_room():
    if request.method == "POST":
        room_name = request.form.get("room_name")
        password = request.form.get("password")

        # ✅ Validation: Check missing form fields
        if not room_name or not password:
            flash("Room name and password are required.")
            return redirect(url_for("create_room"))

        try:
            room = Room(
                room_id=Room.generate_room_id(),
                name=room_name,
                creator=current_user
            )
            room.set_password(password)

            # ✅ Add current user as member
            room.members.append(current_user)

            db.session.add(room)
            db.session.commit()

            return redirect(url_for("view_room", room_id=room.room_id))

        except Exception as e:
            # ✅ Detailed error log
            traceback.print_exc()
            flash("An error occurred while creating the room.")
            return redirect(url_for("create_room"))

    return render_template("create_room.html")

@app.route('/join_room', methods=['GET', 'POST'])
@login_required
def join_room():
    if request.method == 'POST':
        room_id = request.form.get('room_id')
        if room_id:
            room_id = room_id.upper()
        else:
            flash('Room ID is required', 'error')
            return render_template('join_room.html')
        password = request.form.get('password')
        
        room = Room.query.filter_by(room_id=room_id).first()
        
        if not room:
            flash('Room not found', 'error')
            return render_template('join_room.html')
            
        if not room.check_password(password):
            flash('Incorrect password', 'error')
            return render_template('join_room.html')
            
        if current_user not in room.members:
            room.members.append(current_user)
            db.session.commit()
            flash('Successfully joined the room!', 'success')
        else:
            flash('You are already a member of this room', 'info')
            
        return redirect(url_for('room', room_id=room_id))
    
    return render_template('join_room.html')

@app.route('/room/<room_id>')
@login_required
def room(room_id):
    room = Room.query.filter_by(room_id=room_id).first_or_404()
    
    # Check if user is a member
    if current_user not in room.members:
        flash('You are not a member of this room', 'error')
        return redirect(url_for('dashboard'))
    
    is_creator = room.creator_id == current_user.id
    topics = room.topics.order_by(Topic.order_index).all()
    
    # Get user progress for all subtopics
    user_progress = {}
    for topic in topics:
        for subtopic in topic.subtopics:
            progress = UserProgress.query.filter_by(
                user_id=current_user.id, 
                subtopic_id=subtopic.id
            ).first()
            
            if not progress:
                progress = UserProgress()
                progress.user_id = current_user.id
                progress.subtopic_id = subtopic.id
                db.session.add(progress)
                
            user_progress[subtopic.id] = progress
    
    db.session.commit()
    
    # Get room notes
    notes = Note.query.filter_by(room_id=room.id).order_by(Note.created_at.desc()).all()
    
    # Get file notes
    file_notes = FileNote.query.filter_by(room_id=room.id).order_by(FileNote.created_at.desc()).all()
    
    # Calculate total time for each topic
    topic_times = {}
    for topic in topics:
        subtopics_list = list(topic.subtopics)
        total_estimated = sum(subtopic.estimated_time for subtopic in subtopics_list)
        total_actual = 0
        completed_subtopics = 0
        
        for subtopic in subtopics_list:
            if subtopic.id in user_progress:
                total_actual += user_progress[subtopic.id].actual_minutes
                if user_progress[subtopic.id].status == 'completed':
                    completed_subtopics += 1
        
        topic_times[topic.id] = {
            'estimated': total_estimated,
            'actual': total_actual,
            'completed_count': completed_subtopics,
            'total_count': len(subtopics_list)
        }
    
    return render_template('room.html', 
                         room=room, 
                         topics=topics, 
                         user_progress=user_progress,
                         is_creator=is_creator,
                         members=room.members,
                         notes=notes,
                         file_notes=file_notes,
                         topic_times=topic_times)

@app.route('/save_syllabus/<room_id>', methods=['POST'])
@login_required
def save_syllabus(room_id):
    room = Room.query.filter_by(room_id=room_id).first_or_404()
    
    # Check if user is the creator
    if room.creator_id != current_user.id:
        flash('Only the room creator can save the syllabus', 'error')
        return redirect(url_for('room', room_id=room_id))
    
    try:
        data = request.get_json()
        topics_data = data.get('topics', [])
        
        # Clear existing topics
        for topic in room.topics:
            db.session.delete(topic)
        
        # Create new topics and subtopics
        for topic_index, topic_data in enumerate(topics_data):
            topic = Topic()
            topic.name = topic_data['name']
            topic.room_id = room.id
            topic.order_index = topic_index
            db.session.add(topic)
            db.session.flush()  # Get the topic ID
            
            for subtopic_index, subtopic_data in enumerate(topic_data['subtopics']):
                subtopic = Subtopic()
                subtopic.name = subtopic_data['name']
                subtopic.estimated_time = int(subtopic_data['estimated_time'])
                subtopic.topic_id = topic.id
                subtopic.order_index = subtopic_index
                db.session.add(subtopic)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/start_timer', methods=['POST'])
@login_required
def start_timer():
    data = request.get_json()
    subtopic_id = data.get('subtopic_id')
    
    subtopic = Subtopic.query.get_or_404(subtopic_id)
    
    # Create new study session
    session = StudySession()
    session.user_id = current_user.id
    session.subtopic_id = subtopic_id
    session.start_time = datetime.utcnow()
    db.session.add(session)
    
    # Update progress status
    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        subtopic_id=subtopic_id
    ).first()
    
    if progress and progress.status == 'not_started':
        progress.status = 'in_progress'
    
    db.session.commit()
    
    return jsonify({'success': True, 'session_id': session.id})

@app.route('/stop_timer', methods=['POST'])
@login_required
def stop_timer():
    data = request.get_json()
    session_id = data.get('session_id')
    
    session = StudySession.query.get_or_404(session_id)
    
    if session.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    session.end_time = datetime.utcnow()
    duration = session.end_time - session.start_time
    session.duration_minutes = int(duration.total_seconds() / 60)
    
    # Update user progress
    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        subtopic_id=session.subtopic_id
    ).first()
    
    if progress:
        progress.actual_minutes += session.duration_minutes
        progress.updated_at = datetime.utcnow()
    
    # Update user streak
    current_user.update_streak()
    
    db.session.commit()
    
    return jsonify({'success': True, 'duration': session.duration_minutes})

@app.route('/mark_complete', methods=['POST'])
@login_required
def mark_complete():
    data = request.get_json()
    subtopic_id = data.get('subtopic_id')
    completed = data.get('completed', False)
    
    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        subtopic_id=subtopic_id
    ).first()
    
    if progress:
        progress.status = 'completed' if completed else 'in_progress'
        progress.updated_at = datetime.utcnow()
        db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/daily_progress')
@login_required
def api_daily_progress():
    today_minutes = current_user.get_today_minutes()
    daily_goal = current_user.daily_goal_minutes
    progress_percentage = min(100, int((today_minutes / daily_goal) * 100)) if daily_goal > 0 else 0
    
    return jsonify({
        'today_minutes': today_minutes,
        'daily_goal': daily_goal,
        'progress_percentage': progress_percentage,
        'goal_met': today_minutes >= daily_goal,
        'current_streak': current_user.current_streak,
        'longest_streak': current_user.longest_streak
    })

@app.route('/api/room_analytics/<room_id>')
@login_required
def api_room_analytics(room_id):
    room = Room.query.filter_by(room_id=room_id).first_or_404()
    
    if current_user not in room.members:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get user's progress in this room
    topics = room.topics.all()
    total_subtopics = 0
    completed_subtopics = 0
    total_estimated_time = 0
    total_actual_time = 0
    
    for topic in topics:
        for subtopic in topic.subtopics:
            total_subtopics += 1
            total_estimated_time += subtopic.estimated_time
            
            progress = UserProgress.query.filter_by(
                user_id=current_user.id,
                subtopic_id=subtopic.id
            ).first()
            
            if progress:
                total_actual_time += progress.actual_minutes
                if progress.status == 'completed':
                    completed_subtopics += 1
    
    completion_percentage = int((completed_subtopics / total_subtopics) * 100) if total_subtopics > 0 else 0
    
    return jsonify({
        'total_subtopics': total_subtopics,
        'completed_subtopics': completed_subtopics,
        'completion_percentage': completion_percentage,
        'total_estimated_time': total_estimated_time,
        'total_actual_time': total_actual_time
    })

@app.route('/api/room_leaderboard/<room_id>')
@login_required
def api_room_leaderboard(room_id):
    room = Room.query.filter_by(room_id=room_id).first_or_404()
    
    if current_user not in room.members:
        return jsonify({'error': 'Unauthorized'}), 403
    
    leaderboard = []
    
    for member in room.members:
        total_time = 0
        completed_count = 0
        
        for topic in room.topics:
            for subtopic in topic.subtopics:
                progress = UserProgress.query.filter_by(
                    user_id=member.id,
                    subtopic_id=subtopic.id
                ).first()
                
                if progress:
                    total_time += progress.actual_minutes
                    if progress.status == 'completed':
                        completed_count += 1
        
        leaderboard.append({
            'username': member.username,
            'total_time': total_time,
            'completed_count': completed_count,
            'is_current_user': member.id == current_user.id
        })
    
    # Sort by total time descending
    leaderboard.sort(key=lambda x: x['total_time'], reverse=True)
    
    return jsonify(leaderboard)

@app.route('/update_daily_goal', methods=['POST'])
@login_required
def update_daily_goal():
    daily_goal_str = request.form.get('daily_goal')
    if not daily_goal_str:
        flash('Daily goal is required', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        daily_goal = int(daily_goal_str)
    except ValueError:
        flash('Invalid daily goal value', 'error')
        return redirect(url_for('dashboard'))
    
    if daily_goal < 5 or daily_goal > 600:
        flash('Daily goal must be between 5 and 600 minutes', 'error')
    else:
        current_user.daily_goal_minutes = daily_goal
        db.session.commit()
        flash('Daily goal updated successfully', 'success')
    
    return redirect(url_for('dashboard'))

# Notes Routes
@app.route('/add_note/<room_id>', methods=['POST'])
@login_required
def add_note(room_id):
    room = Room.query.filter_by(room_id=room_id).first_or_404()
    
    if current_user not in room.members:
        flash('You are not a member of this room', 'error')
        return redirect(url_for('dashboard'))
    
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Note content cannot be empty', 'error')
        return redirect(url_for('room', room_id=room_id))
    
    note = Note()
    note.content = content
    note.room_id = room.id
    note.author_id = current_user.id
    
    db.session.add(note)
    db.session.commit()
    
    flash('Note added successfully', 'success')
    return redirect(url_for('room', room_id=room_id))

@app.route('/upload_file/<room_id>', methods=['POST'])
@login_required
def upload_file(room_id):
    room = Room.query.filter_by(room_id=room_id).first_or_404()
    
    if current_user not in room.members:
        flash('You are not a member of this room', 'error')
        return redirect(url_for('dashboard'))
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('room', room_id=room_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('room', room_id=room_id))
    
    if file and file.filename:
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        if not original_filename:
            flash('Invalid filename', 'error')
            return redirect(url_for('room', room_id=room_id))
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        
        # Read file data
        file_data = file.read()
        file_size = len(file_data)
        
        # Check file size (limit to 10MB)
        if file_size > 10 * 1024 * 1024:
            flash('File size must be less than 10MB', 'error')
            return redirect(url_for('room', room_id=room_id))
        
        # Create file note record
        file_note = FileNote()
        file_note.filename = unique_filename
        file_note.original_filename = original_filename
        file_note.file_size = file_size
        file_note.mime_type = file.content_type or 'application/octet-stream'
        file_note.file_data = file_data
        file_note.room_id = room.id
        file_note.author_id = current_user.id
        
        db.session.add(file_note)
        db.session.commit()
        
        flash('File uploaded successfully', 'success')
    
    return redirect(url_for('room', room_id=room_id))

@app.route('/download_file/<int:file_id>')
@login_required
def download_file(file_id):
    file_note = FileNote.query.get_or_404(file_id)
    room = file_note.room
    
    # Check if user is a member of the room
    if current_user not in room.members:
        flash('You are not authorized to download this file', 'error')
        return redirect(url_for('dashboard'))
    
    # Create BytesIO object from file data
    file_data = BytesIO(file_note.file_data)
    file_data.seek(0)
    
    return send_file(
        file_data,
        as_attachment=True,
        download_name=file_note.original_filename,
        mimetype=file_note.mime_type
    )

@app.route('/delete_file/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    file_note = FileNote.query.get_or_404(file_id)
    room_id = file_note.room.room_id
    
    if file_note.author_id != current_user.id:
        flash('You can only delete your own files', 'error')
        return redirect(url_for('room', room_id=room_id))
    
    db.session.delete(file_note)
    db.session.commit()
    
    flash('File deleted successfully', 'success')
    return redirect(url_for('room', room_id=room_id))

@app.route('/edit_note/<int:note_id>', methods=['POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    if note.author_id != current_user.id:
        flash('You can only edit your own notes', 'error')
        return redirect(url_for('room', room_id=note.room.room_id))
    
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Note content cannot be empty', 'error')
        return redirect(url_for('room', room_id=note.room.room_id))
    
    note.content = content
    note.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash('Note updated successfully', 'success')
    return redirect(url_for('room', room_id=note.room.room_id))

@app.route('/delete_note/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    room_id = note.room.room_id
    
    if note.author_id != current_user.id:
        flash('You can only delete your own notes', 'error')
        return redirect(url_for('room', room_id=room_id))
    
    db.session.delete(note)
    db.session.commit()
    
    flash('Note deleted successfully', 'success')
    return redirect(url_for('room', room_id=room_id))

@app.route('/api/notes/<room_id>')
@login_required
def api_notes(room_id):
    room = Room.query.filter_by(room_id=room_id).first_or_404()
    
    if current_user not in room.members:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notes = Note.query.filter_by(room_id=room.id).order_by(Note.created_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])
