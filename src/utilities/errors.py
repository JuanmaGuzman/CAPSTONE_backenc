from ninja import Schema


class ErrorsOut(Schema):
    errors: dict[str, list[str]]


class ErrorOut(Schema):
    message: str


def error404(field: str, instance: str):
    return {f'{field}': [f'{instance} with this {field} does not exist']}


def not_found(instance):
    return {'message': f"NotFound: {instance} does not exist"}


def duplicate_instance(instance):
    return {'message': f"Conflict: {instance} already exists"}


def integrity_error():
    return {'message': 'Conflict: Integrity Error'}


def bad_parameters():
    return {'message': "Bad Parameters in the request"}


def missing_permission():
    return {'message': "Missing permissions for this action"}


def inactive_publication():
    return {'message': "The Publication is not active"}


def item_already_exists(dict1, dict2):
    return {"item for that sku": dict1, "your attempted item": dict2}