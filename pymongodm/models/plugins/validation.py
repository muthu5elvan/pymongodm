from pymongodm.models.plugins import Plugin


class schemaValidation(Plugin):
    def __check(self, query):
        return {'success': query.validator.validate(query.fields),
                'errors': query.validator.errors}

    def pre_create(self, query):
        return self.__check(query)

    def pre_update(self, query):
        return self.__check(query)

    def post_create(self, query):
        pass

    def post_update(self, query):
        pass
