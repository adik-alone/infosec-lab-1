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
    barier = request.headers.get('Authorization')
    token = barier.split(' ')[1]
    if not token:
        return jsonify({"error": "Token required"}), 401
    try:
        decode = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        posts = Post.query.all()
        return jsonify([{'id': p.id, 'title': p.title, 'content': p.content, 'user_id': p.user_id} for p in posts])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

@app.route('/api/data', methods=['POST'])
# @jwt_required()
def create_data():
    barier = request.headers.get('Authorization')
    token = barier.split(' ')[1]
    if not token:
        return jsonify({"error": "Token required"}), 401
    try:
        decode = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])

        data = request.get_json()
        usr_title = html.escape(data.get('title'))
        usr_content = html.escape(data.get('content'))

        user_id = User.query.filter_by(login = decode['user']).first().id
        
        post = Post(title=usr_title, content=usr_content, user_id=user_id)
        db.session.add(post)
        db.session.commit()
        return jsonify({'id': post.id}), 201
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        if not User.query.filter_by(login='admin_py').first():
            user = User(login='admin_py')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
    app.run(debug=True)