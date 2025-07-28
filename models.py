from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import string
import random

# Association table for room members
room_members = db.Table('room_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('room_id', db.Integer, db.ForeignKey('room.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Study streak tracking
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_study_date = db.Column(db.Date)
    daily_goal_minutes = db.Column(db.Integer, default=60)
    
    # Relationships
    created_rooms = db.relationship('Room', backref='creator', lazy='dynamic')
    joined_rooms = db.relationship('Room', secondary=room_members, lazy='subquery',
                                 backref=db.backref('members', lazy=True))
    progress = db.relationship('UserProgress', backref='user', lazy='dynamic')
    study_sessions = db.relationship('StudySession', backref='user', lazy='dynamic')
    notes = db.relationship('Note', backref='author', lazy='dynamic')
    file_notes = db.relationship('FileNote', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_streak(self):
        from datetime import date, timedelta
        today = date.today()
        
        if self.last_study_date:
            if self.last_study_date == today:
                return  # Already studied today
            elif self.last_study_date == today - timedelta(days=1):
                self.current_streak += 1
            else:
                self.current_streak = 1
        else:
            self.current_streak = 1
            
        self.last_study_date = today
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
            
        db.session.commit()

    def get_today_minutes(self):
        from datetime import date
        today = date.today()
        sessions = self.study_sessions.filter(
            db.func.date(StudySession.start_time) == today
        ).all()
        return sum(session.duration_minutes for session in sessions if session.duration_minutes)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(8), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    topics = db.relationship('Topic', backref='room', lazy='dynamic', cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='room', lazy='dynamic', cascade='all, delete-orphan')
    file_notes = db.relationship('FileNote', backref='room', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def generate_room_id():
        while True:
            room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Room.query.filter_by(room_id=room_id).first():
                return room_id

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subtopics = db.relationship('Subtopic', backref='topic', lazy='dynamic', cascade='all, delete-orphan')

class Subtopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    estimated_time = db.Column(db.Integer, nullable=False)  # in minutes
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    progress = db.relationship('UserProgress', backref='subtopic', lazy='dynamic')
    study_sessions = db.relationship('StudySession', backref='subtopic', lazy='dynamic')

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subtopic_id = db.Column(db.Integer, db.ForeignKey('subtopic.id'), nullable=False)
    status = db.Column(db.String(20), default='not_started')  # not_started, in_progress, completed
    actual_minutes = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'subtopic_id'),)

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subtopic_id = db.Column(db.Integer, db.ForeignKey('subtopic.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        from app import db
        author = db.session.get(User, self.author_id)
        return {
            'id': self.id,
            'content': self.content,
            'author_name': author.username if author else 'Unknown',
            'author_id': self.author_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class FileNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_data = db.Column(db.LargeBinary, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        from app import db
        author = db.session.get(User, self.author_id)
        return {
            'id': self.id,
            'filename': self.original_filename,
            'file_size': self.file_size,
            'author_name': author.username if author else 'Unknown',
            'author_id': self.author_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
