from flask import jsonify

from project.common.exceptions import APIException, ServerErrorException


def handle_exception(error: APIException):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def handle_general_exception(_):
    return handle_exception(ServerErrorException())