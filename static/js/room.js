// Room functionality for StudySync

let socket;
let topicCount = 1;

// Initialize room functionality
function initializeRoom(roomId, isCreator) {
    // Initialize Socket.IO
    socket = io();
    
    // Join the room
    socket.emit('join_room', { room_id: roomId });
    
    // Socket event listeners
    socket.on('user_joined', function(data) {
        console.log(`${data.username} joined the room`);
        updateActiveUsers();
    });
    
    socket.on('user_left', function(data) {
        console.log(`${data.username} left the room`);
        updateActiveUsers();
    });
    
    socket.on('timer_started', function(data) {
        console.log(`${data.username} started timer for subtopic ${data.subtopic_id}`);
        updateActiveSessions();
    });
    
    socket.on('timer_stopped', function(data) {
        console.log(`${data.username} stopped timer (${data.duration} minutes)`);
        updateActiveSessions();
        updateTotalTime();
    });
    
    socket.on('progress_updated', function(data) {
        console.log(`${data.username} updated progress for subtopic ${data.subtopic_id}`);
    });

    socket.on('note_added', function(note) {
        addNoteToList(note);
    });
    
    // Initialize syllabus form if user is creator
    if (isCreator) {
        initializeSyllabusForm();
    }
}

// Update active sessions count
function updateActiveSessions() {
    // This would typically fetch from server, for now just update UI
    const activeSessionsElement = document.getElementById('activeSessions');
    if (activeSessionsElement) {
        // Count running timers
        const runningTimers = Object.values(timers).filter(timer => timer.isRunning).length;
        activeSessionsElement.textContent = runningTimers;
    }
}

// Update total time
function updateTotalTime() {
    // This would fetch actual data from server
    const totalTimeElement = document.getElementById('totalTime');
    if (totalTimeElement) {
        // For now, just keep existing display
    }
}

// Update active users display
function updateActiveUsers() {
    // This would fetch current room members from server
    // For now, keeping existing display
}

// Initialize syllabus form
function initializeSyllabusForm() {
    const syllabusForm = document.getElementById('syllabusForm');
    if (!syllabusForm) return;
    
    // Add topic button
    document.getElementById('addTopic').addEventListener('click', function() {
        addTopicSection();
    });
    
    // Submit form
    syllabusForm.addEventListener('submit', function(e) {
        e.preventDefault();
        saveSyllabus();
    });
    
    // Initialize existing topic sections
    initializeTopicSection(document.querySelector('.topic-section'));
}

// Add new topic section
function addTopicSection() {
    topicCount++;
    const container = document.getElementById('topicsContainer');
    
    const topicHtml = `
        <div class="topic-section mb-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6>Topic ${topicCount}</h6>
                <button type="button" class="btn btn-outline-danger btn-sm remove-topic">
                    <i class="fas fa-times"></i> Remove Topic
                </button>
            </div>
            <div class="row mb-3">
                <div class="col-md-6">
                    <input type="text" class="form-control topic-name" placeholder="Topic name" required>
                </div>
            </div>
            <div class="subtopics-container">
                <div class="row mb-2 subtopic-row">
                    <div class="col-md-6">
                        <input type="text" class="form-control subtopic-name" placeholder="Subtopic name" required>
                    </div>
                    <div class="col-md-4">
                        <input type="number" class="form-control estimated-time" placeholder="Est. time (minutes)" min="1" required>
                    </div>
                    <div class="col-md-2">
                        <button type="button" class="btn btn-outline-danger btn-sm remove-subtopic">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
            <button type="button" class="btn btn-outline-primary btn-sm add-subtopic">
                <i class="fas fa-plus me-1"></i>Add Subtopic
            </button>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', topicHtml);
    
    // Initialize the new topic section
    const newTopicSection = container.lastElementChild;
    initializeTopicSection(newTopicSection);
}

// Initialize topic section event listeners
function initializeTopicSection(topicSection) {
    if (!topicSection) return;
    
    // Add subtopic button
    const addSubtopicBtn = topicSection.querySelector('.add-subtopic');
    addSubtopicBtn.addEventListener('click', function() {
        addSubtopicRow(topicSection);
    });
    
    // Remove topic button
    const removeTopicBtn = topicSection.querySelector('.remove-topic');
    if (removeTopicBtn) {
        removeTopicBtn.addEventListener('click', function() {
            if (document.querySelectorAll('.topic-section').length > 1) {
                topicSection.remove();
            } else {
                alert('You must have at least one topic.');
            }
        });
    }
    
    // Remove subtopic buttons
    const removeSubtopicBtns = topicSection.querySelectorAll('.remove-subtopic');
    removeSubtopicBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const subtopicRow = this.closest('.subtopic-row');
            const container = subtopicRow.closest('.subtopics-container');
            
            if (container.querySelectorAll('.subtopic-row').length > 1) {
                subtopicRow.remove();
            } else {
                alert('Each topic must have at least one subtopic.');
            }
        });
    });
}

// Add subtopic row
function addSubtopicRow(topicSection) {
    const container = topicSection.querySelector('.subtopics-container');
    
    const subtopicHtml = `
        <div class="row mb-2 subtopic-row">
            <div class="col-md-6">
                <input type="text" class="form-control subtopic-name" placeholder="Subtopic name" required>
            </div>
            <div class="col-md-4">
                <input type="number" class="form-control estimated-time" placeholder="Est. time (minutes)" min="1" required>
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-outline-danger btn-sm remove-subtopic">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', subtopicHtml);
    
    // Add event listener to remove button
    const newRow = container.lastElementChild;
    const removeBtn = newRow.querySelector('.remove-subtopic');
    removeBtn.addEventListener('click', function() {
        if (container.querySelectorAll('.subtopic-row').length > 1) {
            newRow.remove();
        } else {
            alert('Each topic must have at least one subtopic.');
        }
    });
}

// Save syllabus
function saveSyllabus() {
    const topics = [];
    
    document.querySelectorAll('.topic-section').forEach(topicSection => {
        const topicName = topicSection.querySelector('.topic-name').value.trim();
        if (!topicName) return;
        
        const subtopics = [];
        topicSection.querySelectorAll('.subtopic-row').forEach(subtopicRow => {
            const subtopicName = subtopicRow.querySelector('.subtopic-name').value.trim();
            const estimatedTime = parseInt(subtopicRow.querySelector('.estimated-time').value);
            
            if (subtopicName && estimatedTime > 0) {
                subtopics.push({
                    name: subtopicName,
                    estimated_time: estimatedTime
                });
            }
        });
        
        if (subtopics.length > 0) {
            topics.push({
                name: topicName,
                subtopics: subtopics
            });
        }
    });
    
    if (topics.length === 0) {
        alert('Please add at least one topic with subtopics.');
        return;
    }
    
    // Save to server
    fetch(`/save_syllabus/${roomId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topics: topics })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Syllabus saved successfully!');
            location.reload();
        } else {
            alert('Error saving syllabus: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error saving syllabus:', error);
        alert('Error saving syllabus. Please try again.');
    });
}

// Load user analytics
function loadUserAnalytics(roomId) {
    fetch(`/api/room_analytics/${roomId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('analyticsSection').innerHTML = `
                    <div class="text-center text-danger">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span class="ms-2">Error loading analytics</span>
                    </div>
                `;
                return;
            }
            
            const analyticsHtml = `
                <div class="row text-center">
                    <div class="col-6">
                        <div class="h4 text-primary">${data.completed_subtopics}</div>
                        <small class="text-muted">Completed</small>
                    </div>
                    <div class="col-6">
                        <div class="h4">${data.total_subtopics}</div>
                        <small class="text-muted">Total</small>
                    </div>
                </div>
                <div class="progress mb-3" style="height: 20px;">
                    <div class="progress-bar bg-success" style="width: ${data.completion_percentage}%">
                        ${data.completion_percentage}%
                    </div>
                </div>
                <div class="row text-center">
                    <div class="col-6">
                        <div class="h6 text-info">${data.total_actual_time}m</div>
                        <small class="text-muted">Time Spent</small>
                    </div>
                    <div class="col-6">
                        <div class="h6">${data.total_estimated_time}m</div>
                        <small class="text-muted">Estimated</small>
                    </div>
                </div>
            `;
            
            document.getElementById('analyticsSection').innerHTML = analyticsHtml;
        })
        .catch(error => {
            console.error('Error loading analytics:', error);
            document.getElementById('analyticsSection').innerHTML = `
                <div class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span class="ms-2">Error loading analytics</span>
                </div>
            `;
        });
}

// Load room leaderboard
function loadRoomLeaderboard(roomId) {
    fetch(`/api/room_leaderboard/${roomId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('leaderboardSection').innerHTML = `
                    <div class="text-center text-danger">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span class="ms-2">Error loading leaderboard</span>
                    </div>
                `;
                return;
            }
            
            if (data.length === 0) {
                document.getElementById('leaderboardSection').innerHTML = `
                    <div class="text-center text-muted">
                        <i class="fas fa-trophy fa-2x mb-2"></i>
                        <p>No study time recorded yet.</p>
                    </div>
                `;
                return;
            }
            
            let leaderboardHtml = '<div class="list-group list-group-flush">';
            
            data.forEach((member, index) => {
                const badgeClass = index === 0 ? 'bg-warning' : index === 1 ? 'bg-secondary' : 'bg-dark';
                const position = index + 1;
                
                leaderboardHtml += `
                    <div class="list-group-item d-flex justify-content-between align-items-center ${member.is_current_user ? 'border-primary' : ''}">
                        <div>
                            <span class="badge ${badgeClass} me-2">${position}</span>
                            <strong>${member.username}</strong>
                            ${member.is_current_user ? '<small class="text-primary ms-1">(You)</small>' : ''}
                        </div>
                        <div class="text-end">
                            <div class="fw-bold">${member.total_time}m</div>
                            <small class="text-muted">${member.completed_count} completed</small>
                        </div>
                    </div>
                `;
            });
            
            leaderboardHtml += '</div>';
            document.getElementById('leaderboardSection').innerHTML = leaderboardHtml;
        })
        .catch(error => {
            console.error('Error loading leaderboard:', error);
            document.getElementById('leaderboardSection').innerHTML = `
                <div class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span class="ms-2">Error loading leaderboard</span>
                </div>
            `;
        });
}

// Add note to the notes list
function addNoteToList(note) {
    const notesList = document.getElementById('notesList');
    const emptyMessage = notesList.querySelector('.text-center.text-muted');
    
    if (emptyMessage) {
        emptyMessage.remove();
    }
    
    const noteHtml = `
        <div class="note-card card">
            <div class="card-body p-3">
                <p class="mb-2">${note.content}</p>
                <div class="note-meta d-flex justify-content-between align-items-center">
                    <span><i class="fas fa-user me-1"></i>${note.author_name}</span>
                    <small>${note.created_at}</small>
                </div>
            </div>
        </div>
    `;
    
    notesList.insertAdjacentHTML('afterbegin', noteHtml);
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (socket) {
        socket.emit('leave_room', { room_id: roomId });
    }
});
