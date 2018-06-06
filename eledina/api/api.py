# coding=utf-8
from flask import Blueprint, request

from ..flask_util import jsonify_response


__version__ = "0.1.0"


api = Blueprint("eLedinaAPI", __name__,
                static_folder="../../static/", template_folder="../../templates/",
                url_prefix="/api")


@api.route("/version")
def version():
    payload = {
        "version": __version__
    }

    return jsonify_response(payload)

