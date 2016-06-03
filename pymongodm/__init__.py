import pymongo
from pymongo.cursor import Cursor


def connect(odm_database="test", *args, **kwargs):
    global Mongo
    Mongo = pymongo.MongoClient(*args, **kwargs)[odm_database]
    return Mongo


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
