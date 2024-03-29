from travxy.db import db
from travxy.models.place import place_category

class CategoryModel(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    place_details = db.relationship(
            "PlaceModel", secondary=place_category,
            back_populates="categories_info",
            lazy='dynamic', cascade="all, delete")
    place_view = db.relationship(
            "PlaceModel", secondary=place_category,
            back_populates="category",
            viewonly=True)

    def json(self):
        return {'id': self.id, 'name': self.name}

    def with_place_json(self):
        return {'id': self.id, 'name': self.name, 'places': [place.json()
                for place in self.place_details.all()]}

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_all(cls):
        return cls.query.all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


