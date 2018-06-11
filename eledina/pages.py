# coding=utf-8
import os
from flask import Blueprint, render_template, abort


pages = Blueprint("basic_pages", __name__,
                  static_folder="../static/", template_folder="../templates/")


# This renders all pages normally
@pages.route("/<path:template>")
def render(template):
    t = str(template)

    if not t.endswith(".html"):
        t += ".html"

    # TODO check if this can be exploited
    if not os.path.isfile(template):
        return abort(404)

    return render_template(t)
