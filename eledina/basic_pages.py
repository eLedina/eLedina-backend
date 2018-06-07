# coding=utf-8
from flask import Blueprint, render_template


basic_pages = Blueprint("basic_pages", __name__,
                        static_folder="../static/", template_folder="../templates/")


@basic_pages.route("/404")
def basic():
    return render_template("404_example.html")