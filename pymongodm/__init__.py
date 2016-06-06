import pymongo
from pymongo.cursor import Cursor


def connect(database, *args, **kwargs):
    global db
    global Mongo
    if isinstance(database, str):
        db = pymongo.MongoClient(*args, **kwargs)[database]
    else:
        db = database
    # compatibility
    Mongo = db
    return db


def next_converted(self):
    if hasattr(self, "model_type"):
        return self.model_type(self.original_next())
    return self.original_next()


def _set_model(self, model_type):
    self.model_type = model_type
    return self

Cursor.model = _set_model
Cursor.original_next = Cursor.next
Cursor.next = next_converted
Cursor.__next__ = Cursor.next
