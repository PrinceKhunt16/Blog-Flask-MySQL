from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename
import os
import urllib.parse
import json

local_server = True

with open('config.json', 'r') as c:
    params = json.load(c)['params'] 

app = Flask(__name__)

upload_folder = os.path.abspath(params['upload_location'])

app.config['UPLOAD_FOLDER'] = params['upload_location']

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
)

app.secret_key = 'cleanblog'

mail = Mail(app)

password = params['db_password']

encoded_password = urllib.parse.quote_plus(password)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri'].format(encoded_password = encoded_password)
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri'].format(encoded_password = encoded_password)

db = SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), nullable = False)
    phone_num = db.Column(db.String(12), nullable = False)
    msg = db.Column(db.String(120), nullable = False)
    date = db.Column(db.String(12), nullable = True)
    email = db.Column(db.String(20), nullable = False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(80), nullable = False)
    slug = db.Column(db.String(21), nullable = False)
    content = db.Column(db.String(120), nullable = False)
    tagline = db.Column(db.String(120), nullable = False)
    date = db.Column(db.String(12), nullable = True)
    img_file = db.Column(db.String(12), nullable = True)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()[0:5]
    return render_template('index.html', posts = posts)

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/post/<string:post_slug>", methods = ['GET'])
def post(post_slug):
    response = Posts.query.filter_by(slug = post_slug).first()
    return render_template('post.html', response = response)

@app.route("/contact", methods = ["GET", "POST"])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contacts(name = name, email = email, date = datetime.now(), phone_num = phone, msg = message)

        db.session.add(entry)
        db.session.commit()

        mail.send_message('New message from ' + name, sender = email, recipients = [params['gmail_user']], body = message + "\n" + phone)

    return render_template('contact.html')

@app.route("/edit/<string:sno>", methods = ["GET", "POST"])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']): 
        if (request.method == 'POST'):
            title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if (sno == '0'):
                post = Posts(title = title, slug = slug, content = content, tagline = tagline, img_file = img_file, date = date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno = sno).first()
                post.title = title
                post.tagline = tagline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()

                return redirect('/edit/' + sno)
            
        post = Posts.query.filter_by(sno = sno).first()

        return render_template('edit.html', sno = sno, post = post)
    
    return render_template("login.html") 

@app.route("/uploader" , methods = ['POST'])
def uploader():
    if ("user" in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            f = request.files['file']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully."
        
@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>" , methods = ['GET', 'POST'])
def delete(sno):
    if ("user" in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno = sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")

@app.route("/dashboard", methods = ["GET", "POST"])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']): 
        posts = Posts.query.all()
        return render_template('dashboard.html', posts = posts)

    if (request.method == "POST"):
        username = request.form.get("uname")
        userpass = request.form.get("upass")

        if (username == params['admin_user'] and userpass == params['admin_password']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', posts = posts)
    
    return render_template("login.html")

if __name__ == "__main__":
    app.run(port = 5000, debug = True)