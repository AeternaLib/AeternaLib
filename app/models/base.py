from app.extensions import db
from app.exceptions import NotFoundError

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_or_fail(cls, id_):
        obj = db.session.get(cls, id_)
        if obj is None:
            raise NotFoundError(f"{cls.__name__} con id {id_} no existe")
        return obj