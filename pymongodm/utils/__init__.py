class ValidationError(Exception):
    def __init__(self, message):
        super(ValidationError, self).__init__(message)


def dict_diff(x, y):
    return list(set(y.keys()) - set(x.keys()))
