# coding=utf-8
import logging
import os
from flask import Blueprint, render_template, abort, g, request

from core.models import Users


pages = Blueprint("pages", __name__,
                  static_folder="../static/", template_folder="../templates/")

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Extensions to not append .html to
valid_extensions = (
    ".ico",
)

users = Users()


# Set user before request
@pages.before_request
def before_request():
    # check cookies
    access_token = request.cookies.get("accessToken")

    if access_token is not None:
        # get user id
        user_id = users.verify_token(access_token)
        if not user_id:
            return abort(400)

        user_info = users.get_user_info(int(user_id))
        # set 'g' to include logged in user info
        g.user = user_info
    else:
        g.user = {}


# This renders all pages normally
@pages.route("/<path:template>")
def page_render(template):
    t = str(template)
    if not t.endswith(".html") and not t.endswith(valid_extensions):
        t += ".html"

    t_full = os.path.join("templates", t)
    # TODO check if this can be exploited
    if not os.path.isfile(t_full):
        log.info(f"Template requested via page_render() was not found: {t_full}")
        return abort(404)

    return render_template(t)

