from flask import Blueprint, request
from app.models import db, User
from flask_jwt_extended import create_access_token
from datetime import timedelta

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json

    if User.query.filter_by(username=data["username"]).first():
        return {"error": "Username exists"}, 400

    user = User(username=data["username"])
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    return {"message": "User created"}, 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data["username"]).first()

    if not user or not user.check_password(data["password"]):
        return {"error": "Invalid credentials"}, 401

    token = create_access_token(identity=user.id, expires_delta=timedelta(days=1))

    return {"access_token": token}, 200


@auth_bp.route("/me", methods=["GET"])
def me():
    from flask_jwt_extended import get_jwt_identity, jwt_required

    @jwt_required()
    def inner():
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        return {"id": user.id, "username": user.username}

    return inner()