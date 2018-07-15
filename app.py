# coding=utf-8
import logging
from flask import Flask, render_template, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


# 404 error
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# REGISTER BLUEPRINTS
from eledina.pages import pages
app.register_blueprint(pages)

from eledina.api.api_blueprint import api
app.register_blueprint(api)

if __name__ == '__main__':
    app.run(load_dotenv=True)
