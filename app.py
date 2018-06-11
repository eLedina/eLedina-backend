# coding=utf-8

from flask import Flask, render_template, request

app = Flask(__name__)


# index.html
@app.route("/")
def index():
    return render_template("index.html", ip=request.remote_addr)
	
	
# design_page.html
@app.route("/design.html")
def designPage():
    return render_template("design_page.html", ip=request.remote_addr)
	
	
# login.html
@app.route("/login.html")
def login():
    return render_template("login.html", ip=request.remote_addr)
	
	
# register.html
@app.route("/register.html")
def register():
    return render_template("register.html", ip=request.remote_addr)
	
	
# home.html
@app.route("/home.html")
def home():
    return render_template("home.html", ip=request.remote_addr)
	
	
# Blog stuff
@app.route("/blog_main.html")
def blogMain():
    return render_template("blog_mainpage.html", ip=request.remote_addr)
	
@app.route("/blog_writing.html")
def blogWrite():
    return render_template("blog_writingpage.html", ip=request.remote_addr)

@app.route("/blogtemp.html")
def blogTemp():
    return render_template("blogs/blog_sample.html", ip=request.remote_addr)
	

# oral_exam.html
@app.route("/oral_exam.html")
def oralExam():
    return render_template("oral_exam.html", ip=request.remote_addr)
	
@app.route("/oral_exam_list.html")
def oralExamList():
    return render_template("oral_exam_list.html", ip=request.remote_addr)

	
# REGISTER BLUEPRINTS
from eledina.basic_pages import basic_pages
app.register_blueprint(basic_pages)

if __name__ == '__main__':
    app.run(load_dotenv=True)

app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True
)