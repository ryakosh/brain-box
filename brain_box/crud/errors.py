class CRUDError(Exception):
    pass


class AlreadyExistsError(CRUDError):
    pass


class NotFoundError(CRUDError):
    pass
