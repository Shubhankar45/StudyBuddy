// Timer functionality for StudySync

class Timer {
    constructor(subtopicId) {
        this.subtopicId = subtopicId;
        this.sessionId = null;
        this.isRunning = false;
        this.startTime = null;
        this.elapsedTime = 0;
        this.intervalId = null;
        this.displayElement = document.querySelector(`[data-timer="${subtopicId}"]`);
        this.startButton = document.querySelector(`[data-action="start"][data-subtopic="${subtopicId}"]`);
        this.pauseButton = document.querySelector(`[data-action="pause"][data-subtopic="${subtopicId}"]`);
    }

    start() {
        if (this.isRunning) return;

        fetch('/start_timer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                subtopic_id: this.subtopicId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.sessionId = data.session_id;
                this.isRunning = true;
                this.startTime = Date.now() - this.elapsedTime;
                
                this.startButton.classList.add('d-none');
                this.pauseButton.classList.remove('d-none');
                
                this.intervalId = setInterval(() => {
                    this.updateDisplay();
                }, 1000);

                // Emit socket event if available
                if (typeof socket !== 'undefined') {
                    socket.emit('timer_start', {
                        room_id: roomId,
                        subtopic_id: this.subtopicId
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error starting timer:', error);
        });
    }

    pause() {
        if (!this.isRunning) return;

        fetch('/stop_timer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: this.sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.isRunning = false;
                clearInterval(this.intervalId);
                
                this.startButton.classList.remove('d-none');
                this.pauseButton.classList.add('d-none');
                
                // Update actual time in UI
                const row = document.querySelector(`tr[data-subtopic-id="${this.subtopicId}"]`);
                if (row) {
                    const timeCell = row.querySelector('.user-time');
                    const currentTime = parseInt(timeCell.textContent);
                    timeCell.textContent = `${currentTime + data.duration}m`;
                }
                
                this.elapsedTime = 0;
                this.displayElement.textContent = '00:00';

                // Emit socket event if available
                if (typeof socket !== 'undefined') {
                    socket.emit('timer_stop', {
                        room_id: roomId,
                        subtopic_id: this.subtopicId,
                        duration: data.duration
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error stopping timer:', error);
        });
    }

    updateDisplay() {
        if (!this.isRunning) return;
        
        this.elapsedTime = Date.now() - this.startTime;
        const minutes = Math.floor(this.elapsedTime / 60000);
        const seconds = Math.floor((this.elapsedTime % 60000) / 1000);
        
        this.displayElement.textContent = 
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

// Global timers object
const timers = {};

// Initialize timers for all subtopics
document.addEventListener('DOMContentLoaded', function() {
    // Initialize timers
    document.querySelectorAll('[data-timer]').forEach(element => {
        const subtopicId = parseInt(element.dataset.timer);
        timers[subtopicId] = new Timer(subtopicId);
    });

    // Add event listeners for timer buttons
    document.querySelectorAll('.timer-btn').forEach(button => {
        button.addEventListener('click', function() {
            const action = this.dataset.action;
            const subtopicId = parseInt(this.dataset.subtopic);
            
            if (timers[subtopicId]) {
                if (action === 'start') {
                    timers[subtopicId].start();
                } else if (action === 'pause') {
                    timers[subtopicId].pause();
                }
            }
        });
    });

    // Add event listeners for completion checkboxes
    document.querySelectorAll('.completion-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const subtopicId = parseInt(this.dataset.subtopic);
            const completed = this.checked;
            
            fetch('/mark_complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    subtopic_id: subtopicId,
                    completed: completed
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update progress indicator
                    const row = document.querySelector(`tr[data-subtopic-id="${subtopicId}"]`);
                    if (row) {
                        const indicator = row.querySelector('.progress-indicator');
                        indicator.className = `progress-indicator status-${completed ? 'completed' : 'in-progress'}`;
                    }

                    // Emit socket event if available
                    if (typeof socket !== 'undefined') {
                        socket.emit('progress_update', {
                            room_id: roomId,
                            subtopic_id: subtopicId,
                            status: completed ? 'completed' : 'in-progress'
                        });
                    }
                }
            })
            .catch(error => {
                console.error('Error updating completion status:', error);
            });
        });
    });
});
