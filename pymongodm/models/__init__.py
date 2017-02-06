from pymongodm import db, custom_id
from pymongodm.utils import ValidationError
from logging import Logger
from copy import deepcopy
from pymongodm.models.plugins.validation import schemaValidation
from bson import ObjectId
from cerberus import Validator

log = Logger(__name__)


class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class MyValidator(Validator):
    def _validate_type_objectid(*args, **kwargs):
        return True


class Query:
    def __init__(self, model, fields):
        self.validator = MyValidator(model.schema)
        self.fields = fields.copy()

        if custom_id in self.fields:
            del self.fields[custom_id]


class Base:
    def __init__(self, data=None, auto_get=True):
        plugins = [schemaValidation()]

        exclude = ['plugins', 'exclude', 'collection',
                   '_Base__data_loaded']

        # prevent call get()
        self.__data_loaded = True

        if not hasattr(self, "plugins"):
            self.plugins = []
        self.plugins.extend(plugins)

        if not hasattr(self, "exclude"):
            self.exclude = []
        self.exclude.extend(exclude)
        self.collection = self.collect

        # default
        self.__data_loaded = False
        if isinstance(data, dict):
            if custom_id not in data:
                self.create(data)
            else:
                self.__data_loaded = True
                self.__dict__.update(data)

        elif isinstance(data, str):
            setattr(self, custom_id, ObjectId(data))
            if auto_get:
                self.get()
        elif isinstance(data, ObjectId):
            setattr(self, custom_id, data)
            if auto_get:
                self.get()
        elif not data:
            pass
        else:
            raise Exception("invalid format")

    def getattrs(self, exclude_view=False):
        if exclude_view:
            excludes = self.exclude + self.exclude_view
        else:
            excludes = self.exclude
        result = {}
        if not self.__data_loaded:
            self.get()
        for k in self.__dict__:
            if k not in excludes:
                result[k] = self.__dict__[k]
        return result

    def get_clean(self):
        if "exclude_view" in self.__dict__:
            return self.getattrs(True)
        else:
            return self.getattrs(False)

    @ClassProperty
    @classmethod
    def collect(cls):
        if hasattr(cls, "collection_name"):
            return db.get_collection(cls.collection_name)
        return db.get_collection(cls.__module__.split(".")[-1])

    def __iter_plugins(self, action, type_query, fields):
        query = Query(self, fields)
        errors = []
        for plugin in self.plugins:
            r = plugin.__getattribute__('%s_%s' % (action, type_query))(query)
            if r is not None and not r['success']:
                errors.append(r['errors'])

        if len(errors):
            raise ValidationError(errors)

    def update(self, fields=None):
        origin_fields = deepcopy(self.getattrs())
        del origin_fields[custom_id]

        if fields:
            origin_fields.update(fields)
        else:
            fields = origin_fields

        self.__iter_plugins("pre", "update", origin_fields)
        self.collection.update_one({'_id': getattr(self, custom_id)},
                                   {'$set': fields})
        self.__iter_plugins("post", "update", self.get())

    def create(self, fields):
        _id = None
        if custom_id in fields:
            _id = fields.pop(custom_id)

        self.__iter_plugins("pre", "create", fields)

        if _id:
            fields['_id'] = _id

        r = self.collection.insert_one(fields)
        setattr(self, custom_id, r.inserted_id)
        self.__iter_plugins("post", "create", self.get())

    def get(self):
        if custom_id not in self.__dict__:
            return False
        self.__data_loaded = True
        return self.cache(self.collection.find_one,
                          {'_id': getattr(self, custom_id)})

    def remove(self):
        self.collection.remove({'_id': getattr(self, custom_id)})

    def cache(self, query, *args, **kwargs):
        result = query(*args, **kwargs)
        if not result:
            raise ValidationError("return None")

        self.__dict__.update(result)
        return result
