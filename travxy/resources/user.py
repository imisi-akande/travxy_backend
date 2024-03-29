from flask_restful import Resource, request
from datetime import timedelta

from travxy.models.user import UserModel
from travxy.models.tourist import TouristInfoModel
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                get_jwt_identity, jwt_required, get_jwt)

from travxy.blocklist import BLOCKLIST

class UserRegister(Resource):
    def post(self):
        email = request.json.get('email')
        username = request.json.get('username')

        user = UserModel.find_by_email(email)
        username_instance = UserModel.find_by_username(username)

        if user:
            return {"message":"User already exist"}, 400

        if username_instance and username_instance.username == username:
            return {"message":"Username already exist"}, 400

        last_name = request.json.get('last_name')
        first_name = request.json.get('first_name')
        password = request.json.get('password')
        hash_password= UserModel.generate_hash(password)
        data = {'last_name': last_name.title(), 'first_name': first_name.title(),
                'username':username, 'email':email,
                'password':hash_password}
        user = UserModel(**data)
        user.save_to_db()
        return {"message": "User created succesfully"}, 201

class AdminAddUser(Resource):
    @jwt_required()
    def post(self):
        current_identity = get_jwt_identity()
        current_user = UserModel.query.get(current_identity)
        if current_user.role_id != 1:
            return {'message': 'Only Super Admins are allowed'}, 401
        email = request.json.get('email')
        username = request.json.get('username')

        user = UserModel.find_by_email(email)
        username_instance = UserModel.find_by_username(username)

        if user:
            return {"message":"User already exist"}, 400

        if username_instance and username_instance.username == username:
            return {"message":"Username already exist"}, 400

        last_name = request.json.get('last_name')
        first_name = request.json.get('first_name')
        password = request.json.get('password')
        role_id = request.json.get('role_id')
        hash_password= UserModel.generate_hash(password)
        data = {'last_name': last_name.title(), 'first_name': first_name.title(),
                'username':username, 'email':email,
                'password':hash_password, 'role_id': role_id}
        user = UserModel(**data)
        user.save_to_db()
        return {"message": "User created succesfully"}, 201

class AdminForUser(Resource):
    @jwt_required()
    def put(self, user_id):
        current_identity = get_jwt_identity()
        current_user = UserModel.query.get(current_identity)
        if current_user.role_id != 1:
            return {'message': 'Only Super Admins are allowed'}

        last_name = request.json.get('last_name')
        first_name = request.json.get('first_name')
        role_id = request.json.get('role_id')

        user = UserModel.find_by_id(user_id)
        user.last_name = last_name
        user.first_name = first_name
        user.role_id = role_id

        user.save_to_db()
        return {"message": "User updated succesfully"}, 200

    @jwt_required()
    def get(self, user_id):
        current_identity = get_jwt_identity()
        input_user_is_tourist = TouristInfoModel.find_by_user_id(user_id)
        current_user = UserModel.query.get(current_identity)

        if (current_identity) and (current_user.role_id == 1
                                    or current_user.role_id == 2):
            user = UserModel.find_by_id(user_id)
            if not user:
                return {'message': 'User not found'}, 404
            if not input_user_is_tourist:
                return user.json()
            tourist_instance = TouristInfoModel.find_by_user_id(user_id)
            return tourist_instance.json_with_user_detail(), 200
        return {'message': 'Unauthorized User'}, 401

    @jwt_required()
    def delete(self, user_id):
        user_instance = UserModel.query.get(user_id)
        if user_instance is None or user_instance.isactive==False:
            return {'message': 'User does not exist'}, 404
        current_identity = get_jwt_identity()
        current_user = UserModel.query.get(current_identity)

        if current_user.role_id != 1 and current_user.role_id != 2:
            return {'message': 'Unauthorized User'}, 401

        if user_instance.role_id == 1 and current_user.role_id==2:
            return {'message': 'Admin cannot delete SuperAdmin'}, 400

        if user_instance.role_id == 2 and current_user.role_id==2:
            return {'message': 'Admin cannot delete self or other Admins'}, 400

        user_instance.isactive = False
        user_instance.save_to_db()
        return {'message': 'User deleted succesfully'}, 200

class User(Resource):
    @jwt_required()
    def put(self, user_id):
        current_identity = get_jwt_identity()
        if current_identity != user_id:
            return {'message': 'Unauthorized user'}, 401
        last_name = request.json.get('last_name')
        first_name = request.json.get('first_name')

        user = UserModel.find_by_id(user_id)
        user.last_name = last_name
        user.first_name = first_name

        user.save_to_db()
        return {"message": "User updated succesfully"}, 200

    @jwt_required()
    def get(self, user_id):
        current_identity = get_jwt_identity()
        logged_in_user = TouristInfoModel.find_by_user_id(current_identity)
        if logged_in_user is None:
            return {'message':
                        'You must register as a tourist to see other tourists'}, 401
        user = UserModel.find_by_id(user_id)
        user_result = TouristInfoModel.find_by_user_id(user_id)
        if not user or user.isactive==False:
            return {'message': 'User not found'}, 404
        if not user_result or logged_in_user.nationality != user_result.nationality:
            return {'message': 'User does not exist'}, 400
        return user.username_json(), 200

    @jwt_required()
    def delete(self, user_id):
        current_identity = get_jwt_identity()
        user = UserModel.find_by_id(user_id)
        if not user or user.isactive == False:
            return {'message': 'User not found'}, 404
        if user.id != current_identity:
            return {'message': 'Unauthorized User'}, 401
        user.isactive = False
        user.save_to_db()
        return {'message': 'User deleted succesfully'}, 200

class UserAccount(Resource):
     @jwt_required()
     def get(self, user_id):
        current_identity = get_jwt_identity()
        tourist_user = TouristInfoModel.find_by_user_id(current_identity)
        if current_identity != user_id:
            return {'message': 'Unauthorized user'}, 401
        if tourist_user is None:
            return {'message':
                        'Register as a tourist to see account profile'}, 401
        user = UserModel.find_by_id(user_id)
        if not user or user.isactive==False:
            return {'message': 'User not found'}, 404
        return user.username_json(), 200

class UserLogin(Resource):
    def post(self):
        email = request.json.get('email')
        password = request.json.get('password')
        user = UserModel.find_by_email(email)
        if not user:
            return {'message': 'Invalid Credentials'}, 401
        if user.isactive==False:
            return {'message': 'User account does not exist'}, 400
        if user and user.check_hash(password):
            access_token = create_access_token(identity=user.id,
                                                fresh=timedelta(minutes=15))
            refresh_token = create_refresh_token(user.id)
            return {
                'message':'Login suceeded',
                'access_token': access_token,
                'refresh_token': refresh_token
            }, 200

class UserLogout(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out"}, 200

class AdminGetUserList(Resource):
    @jwt_required()
    def get(self):
        current_identity = get_jwt_identity()
        current_user = UserModel.query.get(current_identity)

        if (current_identity) and (current_user.role_id == 1
                                    or current_user.role_id == 2):
            user_instance = UserModel.query.all()
            users = {'users': [user.json()
                                for user in user_instance]}
            return users
        return {'message': 'Unauthorized User'}, 401

class UserList(Resource):
    @jwt_required()
    def get(self):
        current_identity = get_jwt_identity()
        logged_in_user = TouristInfoModel.find_by_user_id(current_identity)
        if logged_in_user is None:
            return {'message':
                    'You must register as a tourist to view all other tourists'}, 400
        logged_in_user_nationality = logged_in_user.nationality

        users = {'users': [user.username_json() for user in UserModel.query.join(
                TouristInfoModel).filter(
                TouristInfoModel.nationality==logged_in_user_nationality).filter(
                UserModel.isactive==True).all()]}
        return users, 200

class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {'access_token': new_token}, 200