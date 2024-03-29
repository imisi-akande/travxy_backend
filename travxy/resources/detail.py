from flask_restful import Resource, request
from travxy.models.detail import DetailModel, tourist_detail
from travxy.models.user import UserModel
from travxy.models.tourist import TouristInfoModel
from travxy.models.place import PlaceModel
from flask_jwt_extended import jwt_required, get_jwt_identity


class DetailList(Resource):
    @jwt_required()
    def post(self):
        current_identity = get_jwt_identity()
        detail_author = TouristInfoModel.find_by_user_id(current_identity)
        if detail_author is None:
            return {'message': 'User is not a registered tourist'}, 401
        place_id = request.json.get('place_id')
        departure = request.json.get('departure')
        transportation = request.json.get('transportation', 'Air')
        travel_buddies = request.json.get('travel_buddies')
        estimated_cost = request.json.get('estimated_cost')
        if not all([place_id, departure, transportation, estimated_cost]):
            return {'message': 'Missing Fields required'}, 400

        if detail_author.user.email in travel_buddies:
            return {'message':
                    'You cannot add yourself into the travel buddy list'}, 400

        place_instance = PlaceModel.find_by_id(place_id)
        if place_instance is None:
            return {'message': 'This place does not exist'}, 400

        tourists = TouristInfoModel.query.join(UserModel).filter(
                        UserModel.email.in_(travel_buddies)).filter(
                        UserModel.isactive==True).filter(
                        TouristInfoModel.nationality==detail_author.nationality).all()
        if len(tourists) != len(travel_buddies):
            return {'message': 'All travel buddies must be registered tourists and must be based in the same location'}, 400

        if len(travel_buddies) > 0:
            detail = DetailModel(place_id=place_id, departure=departure,
                                transportation=transportation,
                                travel_buddies_created_by=detail_author.id,
                                estimated_cost=estimated_cost)
        else:
            detail = DetailModel(place_id=place_id, departure=departure, transportation=transportation,
                                estimated_cost=estimated_cost)

        for tourist in tourists:
            detail.tourists_info.append(tourist)
        detail.tourists_info.append(detail_author)
        try:
            detail.save_to_db()
        except:
            return{'message': 'An error occured while trying to insert details'}, 500
        return detail.json(), 201

    @jwt_required()
    def get(self):
        current_identity = get_jwt_identity()
        detail_author = TouristInfoModel.find_by_user_id(current_identity)
        if detail_author is None:
            return {'message': 'User is not a registered tourist'}, 401

        detail_instances = DetailModel.query.join(TouristInfoModel, UserModel
                                            ).filter(UserModel.isactive==True).filter(
                                            TouristInfoModel.nationality==detail_author.nationality).all()
        details = [detail.with_tourist_json() for detail in detail_instances]
        return details

class Detail(Resource):
    @jwt_required()
    def put(self, detail_id):
        current_identity = get_jwt_identity()
        detail_author = TouristInfoModel.find_by_user_id(current_identity)
        if detail_author is None:
            return {'message': 'User is not a registered tourist'}, 401

        departure = request.json.get('departure')
        transportation = request.json.get('transportation')
        travel_buddies = request.json.get('travel_buddies')
        estimated_cost = request.json.get('estimated_cost')

        detail_instance = DetailModel.find_by_id(detail_id)
        if (detail_instance is None or
                detail_author.id != detail_instance.travel_buddies_created_by):
            return {'message': 'Detail does not exist'}, 400

        if not all([detail_id, departure, transportation, estimated_cost]):
            return {'message': 'Missing Fields required'}, 400

        tourists = TouristInfoModel.query.join(UserModel).filter(
                                    UserModel.email.in_(travel_buddies)
                                    ).filter(UserModel.isactive==True).filter(
                                    TouristInfoModel.nationality==detail_author.nationality
                                    ).all()
        if len(tourists) != len(travel_buddies):
            return {'message':
                        'All travel buddies must be registered tourists and must be based in the same location'}, 400

        if detail_author.user.email in travel_buddies:
            return {'message':
                    'You cannot add yourself into the travel buddy list'}, 400
        tourists.append(detail_author)
        new_travel_buddies = list(set(tourists) - set(
                                        detail_instance.tourists_info.all()))
        to_be_replaced_travel_buddies = list(
                    set(detail_instance.tourists_info.all()) - (set(tourists)))

        detail_instance.id = detail_id
        detail_instance.departure = departure
        detail_instance.transportation = transportation
        detail_instance.estimated_cost = estimated_cost
        for tourist_info in detail_instance.tourists_info:
            if tourist_info in to_be_replaced_travel_buddies:
                detail_instance.tourists_info.remove(tourist_info)
        detail_instance.tourists_info.extend(new_travel_buddies)
        try:
            detail_instance.save_to_db()
        except:
            return{'message':
                        'An error occured while trying to update details'}, 500
        return detail_instance.with_tourist_json()

    @jwt_required()
    def delete(self, detail_id):
        current_identity = get_jwt_identity()
        detail_author = TouristInfoModel.find_by_user_id(current_identity)
        if detail_author is None:
            return {'message': 'User is not a registered tourist'}, 401

        detail_instance = DetailModel.find_by_id(detail_id)
        if (detail_instance is None or
                detail_author.id != detail_instance.travel_buddies_created_by):
            return {'message': 'Detail does not exist'}, 400
        try:
            detail_instance.delete_from_db()
        except:
            return{'message':
                        'An error occured while trying to delete details'}, 500
        return {'message': 'Detail deleted succesfully'}

class GetTouristDetail(Resource):
    @jwt_required()
    def get(self, tourist_id, detail_id):
        current_identity = get_jwt_identity()
        current_user = TouristInfoModel.find_by_user_id(current_identity)
        if current_user is None:
            return {'message': 'User is not a registered tourist'}, 401

        inactive_users = TouristInfoModel.query.join(UserModel).filter(
                                        UserModel.isactive==False).all()
        inactive_tourists_list = []
        for instance in inactive_users:
            inactive_tourists_list.append(instance.id)
        detail_instances = DetailModel.query.join(tourist_detail).join(
                           TouristInfoModel).filter(
                            (tourist_detail.c.detail_id==detail_id) & (
                            tourist_detail.c.tourist_id == tourist_id)).filter(
                            TouristInfoModel.id.notin_(
                            inactive_tourists_list)).first()
        if not detail_instances:
            return {'message': 'Tourist Detail does not exist'}, 400
        return detail_instances.with_tourist_json()

class DetailSpecificToAccount(Resource):
    @jwt_required()
    def get(self):
        current_identity = get_jwt_identity()
        tourist_user = TouristInfoModel.find_by_user_id(current_identity)
        if tourist_user is None:
            return {'message': 'User is not a registered tourist'}, 401
        detail_instances = DetailModel.query.join(tourist_detail).join(
                           TouristInfoModel).filter((
                            tourist_detail.c.tourist_id == tourist_user.id)).all()
        detail_result = [detail_instance.with_tourist_json()
                            for detail_instance in detail_instances]
        if not detail_result:
            return {'message': 'User has no travel history'}, 404
        return detail_result
