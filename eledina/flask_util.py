# coding=utf-8
from flask.wrappers import Response
try:
    from ujson import dumps
except ImportError:
    from json import dumps


def jsonify_response(json, resp_code: int=200):
    return Response(dumps(json), resp_code, mimetype="application/json")
