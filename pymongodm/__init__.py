import pymongo
from pymongo.cursor import Cursor

# in db not rename field
custom_id = '_id'


def connect(database, *args, **kwargs):
    global db
    global conn
    global Mongo
    if isinstance(database, str):
        conn = pymongo.MongoClient(*args, **kwargs)
        db = conn[database]
    else:
        db = database
    # compatibility
    Mongo = db
    return db


def next_converted(self):
    def replace_id(result):
        if '_id' in result:
            result[custom_id] = result.pop('_id')
        return result

    if hasattr(self, "model_type"):
        return self.model_type(replace_id(self.original_next()))
    return replace_id(self.original_next())


def _set_model(self, model_type):
    self.model_type = model_type
    return self


Cursor.model = _set_model
Cursor.original_next = Cursor.next
Cursor.next = next_converted
Cursor.__next__ = Cursor.next
