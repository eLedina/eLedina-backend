# coding=utf-8
from flask.wrappers import Response
from ujson import dumps


def jsonify_response(json, resp_code: int=200):
    return Response(dumps(json), resp_code, mimetype="application/json")
