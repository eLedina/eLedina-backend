# coding=utf-8
import logging
import os
from flask import Blueprint, render_template, abort


pages = Blueprint("pages", __name__,
                  static_folder="../static/", template_folder="../templates/")

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


# This renders all pages normally
@pages.route("/<path:template>")
def page_render(template):
    t = str(template)
    if not t.endswith(".html"):
        t += ".html"

    t_full = os.path.join("templates", t)
    # TODO check if this can be exploited
    if not os.path.isfile(t_full):
        log.info(f"Template requested via page_render() was not found: {t_full}")
        return abort(404)

    return render_template(t)
