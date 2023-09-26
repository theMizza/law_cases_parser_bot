from peewee import *
import os
import functools

database = os.environ.get("MYSQL_DATABASE", "default_value")
user = os.environ.get("MYSQL_USER", "default_value")
password = os.environ.get("MYSQL_PASSWORD", "default_value")
db = MySQLDatabase(database, user=user, password=password, host='db', port=3306)


class DatabaseConnection:
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        self.db.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()


def with_db_connection(db):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            with db.connection_context():
                return f(*args, **kwargs)
        return wrapper
    return decorator


class BaseModel(Model):
    class Meta:
        database = db


class Users(BaseModel):
    user_id = BigIntegerField(unique=True)
    user_phone = CharField(null=True)
    is_admin = BooleanField(default=False)
    is_active = BooleanField(default=False)


class Cases(BaseModel):
    user = ForeignKeyField(Users, backref='cases', on_delete='CASCADE')
    name = CharField()
    url = CharField(null=True)
    case_num = CharField(null=True)
    court_name = CharField(null=True)


class CaseData(BaseModel):
    case = ForeignKeyField(Cases, backref='case_data', on_delete='CASCADE')
    name = CharField()
    value = CharField()


class CaseMovements(BaseModel):
    case = ForeignKeyField(Cases, backref='movements', on_delete='CASCADE')
    event_name = CharField(null=True)
    date = CharField(null=True)
    time = CharField(null=True)
    place = CharField(null=True)
    result = CharField(null=True)
    reason = CharField(null=True)
    add_info = CharField(null=True)
    place_date = CharField(null=True)


class CaseSides(BaseModel):
    case = ForeignKeyField(Cases, backref='sides', on_delete='CASCADE')
    side_type = CharField()
    lastname = CharField()
    inn = CharField()
    kpp = CharField()
    ogrn = CharField()
    ogrnip = CharField()


class ExecutiveLists(BaseModel):
    case = ForeignKeyField(Cases, backref='executive_lists', on_delete='CASCADE')
    date = CharField(null=True)
    num = CharField(null=True)
    el_num = CharField(null=True)
    status = CharField(null=True)
    person = CharField(null=True)
