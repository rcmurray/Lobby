from flask import Flask
from flask import url_for
from markupsafe import escape

from lobby import *


app = Flask(__name__)

@app.route("/")
def index():
    return 'Index Page'

@app.route('/login')
def login():
    return 'login'

@app.get('/login/<username>')
def login_post(username):
    global users
    new_user(username)
    # return str(users[-1]['start_time'])
    # return (users[username]['room'])
    # return str((users[username]['start_time']))
    # return new_user({escape(username)})
    assign_rooms()
    user = users[username]
    if user['room'] is None:
        return "Lobby URL: ..."
    else:
        return user['room']

@app.route('/hello')
def hello():
    return 'Hello, World'


@app.route('/hello_fancy')
def hello_world():
    return "<p>Hello, World! Fancy!</p>"

@app.route('/user/<username>')
def profile(username):
    # show the user profile for that user
    return f'User {escape(username)}'

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return f'Post {post_id}'

@app.route('/path/<path:subpath>')
def show_subpath(subpath):
    # show the subpath after /path/
    return f'Subpath {escape(subpath)}'
#
# with app.test_request_context():
#     print(url_for('index'))
#     print(url_for('login'))
#     print(url_for('login', next='/'))
#     print(url_for('profile', username='John Doe'))

# def new_user(username):
#     if username == "Robbie":
#         return "Numma 1 User"
#     else:
#         return "You not Numma 1 User. Try harder."