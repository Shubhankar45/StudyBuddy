
# 📚StudyBuddy

A real-time web-based chat application built with Python and Flask-SocketIO, enabling seamless communication between users in an interactive environment.

---

## ✨ Features

- 🔐 User authentication (Login/Registration)
- 💬 Real-time messaging with WebSockets
- 👥 Multiple users in a chatroom
- 🗂 Modular project structure
- ⚡ Built with Flask-SocketIO for real-time interaction

---

## 📁 Project Structure

```
ChatRoom/
│
├── app.py                # Flask app initialization
├── main.py               # Entry point to run the app
├── models.py             # Database models for users/messages
├── routes.py             # Application routes
├── socket_events.py      # WebSocket event handlers
├── pyproject.toml        # Python dependencies and metadata
└── .git/                 # Git version control folder
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Shubhankar45/StudyBuddy.git
cd StudyBuddy
```

### 2. Install dependencies

Using pip:

```bash
pip install -r requirements.txt
```

Or with Poetry:

```bash
poetry install
```

### 3. Run the application

```bash
python main.py
```

Then open your browser and visit:  
**http://localhost:5000**

---

## ⚙️ Tech Stack

- **Backend**: Python, Flask
- **WebSockets**: Flask-SocketIO
- **Frontend**: HTML, CSS, Jinja2
- **Database**: SQLite

---

## 🧑‍💻 Author

**Shubhankar45**  
🔗 [GitHub Profile](https://github.com/Shubhankar45)

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 📷 Screenshots (Optional)

_Add screenshots of your chat interface here to make the repo more appealing!_
