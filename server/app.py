#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe, UserSchema, RecipeSchema

class Signup(Resource):
    def post(self):
        json_data = request.get_json()
        if not json_data:
            return {"errors": ["Invalid JSON request"]}, 422
        
        username = json_data.get('username')
        password = json_data.get('password')
        bio = json_data.get('bio')
        image_url = json_data.get('image_url')
        
        if not username or not password:
            return {"errors": ["Username and password are required"]}, 422
        
        try:
            new_user = User(
                username=username,
                bio=bio,
                image_url=image_url
            )
            new_user.password_hash = password
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            return UserSchema().dump(new_user), 201
        except (ValueError, IntegrityError) as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Unauthorized"}, 401
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return {"error": "Unauthorized"}, 401
        return UserSchema().dump(user), 200

class Login(Resource):
    def post(self):
        json_data = request.get_json()
        if not json_data:
            return {"error": "Unauthorized"}, 401
        username = json_data.get('username')
        password = json_data.get('password')
        if not username or not password:
            return {"error": "Unauthorized"}, 401
        user = User.query.filter_by(username=username).first()
        if not user or not user.authenticate(password):
            return {"error": "Unauthorized"}, 401
        session['user_id'] = user.id
        return UserSchema().dump(user), 200

class Logout(Resource):
    def delete(self):
        if 'user_id' not in session or not session['user_id']:
            return {"error": "Unauthorized"}, 401
        session['user_id'] = None
        return {}, 204

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Unauthorized"}, 401
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return {"error": "Unauthorized"}, 401
        recipes = Recipe.query.filter_by(user_id=user.id).all()
        return RecipeSchema(many=True).dump(recipes), 200
    
    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Unauthorized"}, 401
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return {"error": "Unauthorized"}, 401
        
        json_data = request.get_json()
        if not json_data:
            return {"errors": ["Invalid JSON request"]}, 422
        
        title = json_data.get('title')
        instructions = json_data.get('instructions')
        minutes_to_complete = json_data.get('minutes_to_complete')
        
        try:
            recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=user.id
            )
            db.session.add(recipe)
            db.session.commit()
            return RecipeSchema().dump(recipe), 201
        except (ValueError, IntegrityError) as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)