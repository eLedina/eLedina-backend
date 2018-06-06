# coding=utf-8

from flask import Flask, render_template, request

app = Flask(__name__)

# index.html
@app.route("/")
def index():
    return render_template("index.html", ip=request.remote_addr)
	
# design_page.html
@app.route("/design")
def designPage():
    return render_template("design_page.html", ip=request.remote_addr)
	
# login_page.html
@app.route("/login")
def login():
    return render_template("login.html", ip=request.remote_addr)

# REGISTER BLUEPRINTS
from eledina.basic_pages import basic_pages
app.register_blueprint(basic_pages)

if __name__ == '__main__':
    app.run(load_dotenv=True)

app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True
)