from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
import os
import datetime
from dotenv import load_dotenv
from model import db, User, Post
import html

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
db.init_app(app)

@app.before_request
def check_jwt():
    if request.path.startswith('/api/'):
        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return jsonify({"error": "Token required"}), 401
        token = auth.split(' ')[1]
        try:
            jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401


@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')

    user = User.query.filter_by(login=data['login']).first()
    if user and user.check_password(password):
        token = jwt.encode({
            'user': login,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        return jsonify(access_token=token), 200
    return jsonify({"msg": "Bad username or password"}), 401

@app.route('/api/data', methods=['GET'])
def get_data():
    posts = Post.query.all()
    return jsonify([{'id': p.id, 'title': p.title, 'content': p.content, 'user_id': p.user_id} for p in posts])

@app.route('/api/data', methods=['POST'])
def create_data():
    auth = request.headers.get('Authorization')
    token = auth.split(' ')[1]
    decode = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])

    data = request.get_json()
    usr_title = html.escape(data.get('title'))
    usr_content = html.escape(data.get('content'))

    user_id = User.query.filter_by(login = decode['user']).first().id
    
    post = Post(title=usr_title, content=usr_content, user_id=user_id)
    db.session.add(post)
    db.session.commit()
    return jsonify({'id': post.id}), 201

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(login='admin_py').first():
            user = User(login='admin_py')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
    app.run(debug=False, host='localhost', port=5000)