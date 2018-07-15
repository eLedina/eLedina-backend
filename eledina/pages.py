# coding=utf-8
import logging
import time
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
    ######################################
    # 1. ADD ABILITY TO CHECK REQUEST TIME
    # via g.render_time()
    # Adapted from https://gist.github.com/lost-theory/4521102
    ######################################
    g.request_start_time = time.time()
    g.request_time = lambda: str(round(time.time() - g.request_start_time, 4))

    ###################################
    # 2. PARSE COOKIE TO GET USER ID
    ###################################

    # check cookies
    access_token = request.cookies.get("accessToken")

    if access_token is not None:
        # get user id
        user_id = users.verify_token(access_token)
        log.debug(f"From token got userid: {user_id}")

        if not user_id:
            return abort(403)

        user_info = users.get_user_info(int(user_id))
        # set 'g' to include logged in user info
        g.user = user_info
    else:
        g.user = {}


# This renders all pages normally
@pages.route("/")
@pages.route("/<path:template>")
def page_render(template=None):
    if template is None:
        # index.html route triggered
        template = "index.html"

    if not template.endswith(".html") and not template.endswith(valid_extensions):
        template += ".html"

    t_full = os.path.join("templates", template)
    # TODO check if this can be exploited
    if not os.path.isfile(t_full):
        log.info(f"Template requested via page_render() was not found: {t_full}")
        return abort(404)

    return render_template(template)

