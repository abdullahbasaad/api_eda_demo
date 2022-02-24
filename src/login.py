from constants.http_status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import validators
from db import User, db
from auth import requires_auth

login_auth = Blueprint("login_auth", __name__)

global user_id
user_id = None

# Endpoint for registering a new account.
##=======================================
@login_auth.route('/register', methods=['POST'])
#@login_auth.post('/register')
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    if len(password) < 6:
        return jsonify({'error': "Password is too short"}), HTTP_400_BAD_REQUEST

    if len(username) < 3:
        return jsonify({'error': "User is too short"}), HTTP_400_BAD_REQUEST

    if not username.isalnum() or " " in username:
        return jsonify({'error': "Username should be alphanumeric, also no spaces"}), HTTP_400_BAD_REQUEST

    if not validators.email(email):
        return jsonify({'error': "Email is not valid"}), HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': "Email is taken"}), HTTP_409_CONFLICT

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({'error': "username is taken"}), HTTP_409_CONFLICT

    pwd_hash = generate_password_hash(password)

    user = User(username=username, password=pwd_hash, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': "User created",
        'user': {
            'username': username, "email": email
        }

    }), HTTP_201_CREATED

# Endpoint for login. I passed a user id 
# to use it in all endpoints in the API.
##=======================================
@login_auth.route('/login', methods=['POST'])
#@login_auth.post('/login')
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    user = User.query.filter_by(email=email).first()

    if user:
        is_pass_correct = check_password_hash(user.password, password)

        if is_pass_correct:
            global user_id
            user_id = user.id
            return jsonify({
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'Userid': user.id
                }

            }), HTTP_200_OK
    
    user_id = None
    return jsonify({'error': 'Wrong credentials'}), HTTP_401_UNAUTHORIZED

# Helping function to call it from everywhere
# in the API to return current user info.
##=======================================
def return_user():
    return user_id

# Endpoint to return the current account
##=======================================
@login_auth.route('/me', methods=['GET'])
#@login_auth.get("/me")
@requires_auth
def me():
    user_id = return_user()
    if user_id != None:
        user = User.query.filter_by(id=user_id).first()

        return jsonify({
            'username': user.username,
            'email': user.email
        }), HTTP_200_OK
    else:
        return jsonify({"message":"No user..."}), HTTP_404_NOT_FOUND

