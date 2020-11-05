import json

from flask_login import UserMixin
from sqlalchemy.types import TypeDecorator, VARCHAR
from werkzeug.security import generate_password_hash, check_password_hash

from server.course_monitor.database import db


class JsonEncoded(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""

    # @property
    # def python_type(self):
    #     pass
    #
    # def process_literal_param(self, value, dialect):
    #     pass

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is None:
            return '[]'
        else:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        else:
            return json.loads(value)


class User(UserMixin, db.Model):
    uid = db.Column(db.String(7), primary_key=True)
    password_hash = db.Column(db.String(1000))
    cookies = db.Column(JsonEncoded())

    def __init__(self, usr_name, password):
        self.uid = usr_name
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.uid
