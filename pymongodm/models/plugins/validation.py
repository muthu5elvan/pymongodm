from pymongodm.utils import ValidationError
from pymongodm.utils import dict_diff
from pymongodm.models.plugins import Plugin


class FunctionValidation(Plugin):
    def __check(self, query):
        for field, value in query.fields.items():
            validation = query.model.validation_map[field]
            if 'function' in validation:
                if isinstance(validation['function'], list):
                    for val in validation['function']:
                        if not val(value):
                            raise ValidationError("FunctionValidation error")
                else:
                    if not validation['function'](value):
                        raise ValidationError("FunctionValidation error")

    def pre_create(self, query):
        return self.__check(query)

    def pre_update(self, query):
        return self.__check(query)


class RequireValidation(Plugin):
    def __check(self, query):
        not_exists = dict_diff(query.model.validation_map, query.fields)
        if not_exists:
            raise ValidationError("Key not exist")

    def pre_create(self, query):
        self.__check(query)
        missings = dict_diff(query.fields, query.model.validation_map)
        for missing in missings:
            if query.model.validation_map[missing].get("require", False):
                raise ValidationError("missings keys")

    def pre_update(self, query):
        self.__check(query)


class TypeValidation(Plugin):
    def __check(self, query):
        for field, value in query.fields.items():
            validation = query.model.validation_map[field]
            if not isinstance(value, validation['type']):
                raise ValidationError("Type validation error")

    def pre_create(self, query):
        return self.__check(query)

    def pre_update(self, query):
        return self.__check(query)