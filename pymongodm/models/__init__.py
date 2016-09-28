import copy
from pymongodm import db
from pymongodm.utils import ValidationError
from logging import Logger
from copy import deepcopy
from pymongodm.models.plugins.validation import RequireValidation
from pymongodm.models.plugins.validation import FunctionValidation
from pymongodm.models.plugins.validation import TypeValidation

log = Logger(__name__)


class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


def generate_map(value, last=True, path=None, result=None):
    if result is None:
        result = {}

    if path is None:
        path = []

    for key, val in value.items():
        copy_path = copy.deepcopy(path)
        if not isinstance(val, dict):
            if not last:
                result[".".join(copy_path)] = value
                break
            copy_path.append(key)
            result[".".join(copy_path)] = val
        else:
            copy_path.append(key)
            generate_map(val, last, copy_path, result)
    # import ipdb; ipdb.set_trace()
    return result


class Query:
    def __init__(self, type, model=None, projections=None,
                 conditions=None, fields=None):
        self.model = model
        if projections:
            self.projections = generate_map(projections)
        if conditions:
            self.conditions = generate_map(conditions)
        if fields:
            self.fields = generate_map(fields)


class Base:
    def __generate_map(self, *args, **kwargs):
        return generate_map(*args, **kwargs)

    def __init__(self, data=None, auto_get=True):
        plugins = [RequireValidation(), TypeValidation(),
                   FunctionValidation()]

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

        if not hasattr(self, "validation_map"):
            # modify original class (not instance!)
            self.__class__.validation_map = self.__generate_map(self.schema,
                                                                False)

        # default
        self.__data_loaded = False

        if isinstance(data, dict):
            self.create(data)

        elif isinstance(data, str):
            self._id = data
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

    def __iter_plugins(self, type_query, fields):
        query = Query(type_query, self, fields=fields)
        errors = []
        for plugin in self.plugins:
            try:
                if '_id' in query.fields:
                    del query.fields['_id']
                plugin.__getattribute__('pre_%s' % type_query)(query)
            except StopIteration:
                pass
            except Exception as ex:
                errors.append([plugin, ex])
        if len(errors):
            raise ValidationError(errors)

    def update(self, fields=None):
        if not fields:
            fields = deepcopy(self.getattrs())
            del fields['_id']
        self.__iter_plugins("update", fields)
        self.collection.update_one({'_id': self._id},
                                   {'$set': fields})
        self.get()

    def insert(self, fields=None):
        if not fields:
            fields = deepcopy(self.getattrs())
        self.__iter_plugins("create", fields)
        self.collection.insert_one(fields)
        self.get()

    def define(self, fields):
        self.__data_loaded = True
        self.__iter_plugins("create", fields)
        self.__dict__.update(fields)

    def create(self, fields):
        self.__iter_plugins("create", fields)
        self.collection.insert_one(fields)
        self.__dict__.update(fields)

    def get(self):
        if "_id" not in self.__dict__:
            return False
        self.__data_loaded = True
        return self.cache(self.collection.find_one,
                          {'_id': self._id})

    def remove(self):
        self.collection.remove_one({'_id': self._id})

    def cache(self, query, *args, **kwargs):
        result = query(*args, **kwargs)
        if not result:
            raise ValidationError("return None")
        self.__dict__.update(result)
        return result
