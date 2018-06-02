# coding=utf-8

from flask import Flask, render_template, request

app = Flask(__name__)


# index.html
@app.route("/")
def index():
    return render_template("index_example.html", ip=request.remote_addr)


# REGISTER BLUEPRINTS
from eledina.basic_pages import basic_pages
app.register_blueprint(basic_pages)

if __name__ == '__main__':
    app.run(load_dotenv=True)

