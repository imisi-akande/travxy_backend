from travxy.models.tourist import TouristInfoModel
from travxy.models.tour import TourModel
from travxy.models.detail import DetailModel
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload


class TouristList(Resource):

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        if TouristInfoModel.find_by_user_id(user_id):
            return {'message': "A tourist with userid '{}' already exists".format(user_id)}, 400

        nationality = request.json.get('nationality')
        gender = request.json.get('gender', 'Neutral')
        role_id = request.json.get('role_id')
        if not all([nationality, gender]):
            return {'message': 'Missing Fields required'}, 400
        tourist = TouristInfoModel(nationality=nationality, gender=gender,
                                   user_id=user_id, role_id=role_id)
        try:
            tourist.save_to_db()
        except:
            return {'message': 'An error occured while creating tourists'}, 500
        return tourist.json(), 201

    @jwt_required()
    def put(self):
        user_id = get_jwt_identity()
        tourist_user = TouristInfoModel.find_by_user_id(user_id)

        nationality = request.json.get('nationality')
        gender = request.json.get('gender')
        tourist_user.nationality = nationality
        tourist_user.gender = gender
        try:
            tourist_user.save_to_db()
        except:
            return {'message': 'An error occured while editing tourists'}, 500
        return tourist_user.json()

class TouristDetail(Resource):
    @jwt_required()
    def post(self):
        current_identity = get_jwt_identity()
        tourist_user = TouristInfoModel.find_by_user_id(current_identity)
        if tourist_user is None:
            return {'message': 'User is not a registered tourist'}

        tour_id = request.json.get('tour_id')
        departure = request.json.get('departure')
        transportation = request.json.get('transportation')
        estimated_cost = request.json.get('estimated_cost')
        if not all([tour_id, departure, transportation, estimated_cost]):
            return {'message': 'Missing Required Fields'}, 400
        tour_instance = TourModel.find_by_id(tour_id)

        if tour_instance is None:
            return {'message': 'This tour name does not exist'}, 400

        detail = DetailModel(tour_id=tour_id, departure=departure,
                            transportation=transportation,
                            estimated_cost=estimated_cost)
        tourist_user.tour_details_of_tourists.append(detail)
        try:
            tourist_user.save_to_db()
        except:
            return{'message': 'An error occured while trying to insert details'}, 500
        return tourist_user.with_details_json(), 201

    @jwt_required()
    def get(self):
        tourist_instances = TouristInfoModel.query.options(joinedload('details_info'))
        tourists = [tourist.with_details_json() for tourist in tourist_instances]
        return tourists


class AdminTouristList(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        tourist_user = TouristInfoModel.find_by_user_id(user_id)
        if tourist_user.role_id == 1 or tourist_user.role_id == 2:
            tourists = TouristInfoModel.find_all()
            return {'tourists': [tourist.json_with_role() for tourist in tourists]}
        return {'message': 'Unauthorized User'}

    @jwt_required()
    def put(self):
        user_id = get_jwt_identity()
        current_user = TouristInfoModel.find_by_user_id(user_id)
        if current_user.role_id != 1 and current_user.role_id != 2:
            return {'message': 'Unauthorized User'}
        tourist_id = request.json.get('tourist_id')
        tourist_instance = TouristInfoModel.query.get(tourist_id)
        if tourist_instance is None:
            return {'message': 'tourist id does not exist'}, 400
        nationality = request.json.get('nationality')
        gender = request.json.get('gender')
        role_id = request.json.get('role_id')
        if not all([tourist_id, nationality, gender, role_id]):
            return {'message': 'Missing Fields required'}

        tourist_instance.nationality = nationality
        tourist_instance.gender = gender
        tourist_instance.role_id = role_id

        try:
            tourist_instance.save_to_db()
        except:
            return {'message': 'An error occured while editing tourists'}, 500
        return tourist_instance.json_with_role()

class AdminForSpecificTourist(Resource):
    @jwt_required()
    def get(self, tourist_id):
        user_id = get_jwt_identity()
        current_user = TouristInfoModel.find_by_user_id(user_id)
        tourist = TouristInfoModel.query.get(tourist_id)
        if tourist is None:
            return {'message': 'tourist does not exist'}, 404
        if current_user.role_id == 1 or current_user.role_id == 2:
            return tourist.json_with_role()
        return {'message': 'Unauthorized User'}
