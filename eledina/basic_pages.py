# coding=utf-8
from flask import Blueprint, render_template


basic_pages = Blueprint("basic_pages", __name__,
                        static_folder="../static/", template_folder="../templates/")

# This renders all pages normally
@basic_pages.route("/<path:template>")
def render(template):
    t = str(template)

    if not t.endswith(".html"):
        t += ".html"

    return render_template(t)
