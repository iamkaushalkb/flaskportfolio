#Importing Modules
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from  werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Mail
import json
import os
import math

#Reading JSON file
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

#app_configuration
local_server = True
app = Flask(__name__)
#Upload Location
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.secret_key = "#kaushal"
#app configuration for mail system
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app)
#For Datavase Server
#Local and Production URI which is same for now
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)

#Class Section
#creating class for contact db
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cname = db.Column(db.String(80), nullable=False)
    cemail = db.Column(db.String(20), nullable=False)
    csubject = db.Column(db.String(12), nullable=False)
    cmsg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
#creating class for post db
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
#creating class for feedback db
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(21), nullable=False)
    feedback = db.Column(db.String(120), nullable=False)
    img = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    
#Routing Page
@app.route("/dashboard",  methods = ['GET', 'POST'])
def dashboard():
    #if user is already logged in
    if('user' in session and session['user'] == params['admin_user']):
        posts = Post.query.filter_by().all()
        return render_template('dashboard.html', params=params, posts=posts)
    #for login
    if(request.method=='POST'):
        username = request.form.get('uname')
        password = request.form.get('pass')
        if(username == params['admin_user'] and password == params['admin_password']):
            #Setting Session Variable
            session['user'] = username
            posts = Post.query.filter_by().all()
            return render_template('dashboard.html', params=params, posts=posts)
    return render_template('signin.html', params=params)

@app.route("/")
def home():
    #displaying post
    #its pagination
    #For pagination "page" is used
    posts = Post.query.filter_by().all()
    #Pagination Logic
    last = math.ceil(len(posts)/int((params['no_of_posts'])))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts  =posts[(page-1)*int((params['no_of_posts'])):(page-1)*int((params['no_of_posts']))+int((params['no_of_posts']))]
    #first_page
    if (page == 1):
        prevp = '#'
        nextp = "/?page="+str(page + 1)
    #last_page
    elif (page==last):
        prevp = "/?page="+str(page - 1)
        nextp = "#"
    #middle_page
    else:
         prevp = "/?page="+str(page - 1)
         nextp = "/?page="+str(page + 1)
         
    #displaying feedbacks and 
    #its pagination
    #For pagination "pagef" is used
    feedbacks = Feedback.query.filter_by().all()
    #Pagination Logic
    last = math.ceil(len(feedbacks)/int((params['no_of_posts'])))
    pagef = request.args.get('pagef')
    if(not str(pagef).isnumeric()):
        pagef = 1
    pagef = int(pagef)
    feedbacks  =feedbacks[(pagef-1)*int((params['no_of_posts'])):(pagef-1)*int((params['no_of_posts']))+int((params['no_of_posts']))]
    #first_page
    if (pagef == 1):
        prevf = '#'
        nextf= "/?pagef="+str(pagef + 1)
    elif (pagef==last):
        prevf = "/?pagef="+str(pagef - 1)
        nextf = "#"
    else:
         prevf = "/?pagef="+str(pagef - 1)
         nextf = "/?pagef="+str(pagef + 1)
    return render_template('index.html', params=params, posts=posts , feedbacks=feedbacks, prevp=prevp, nextp=nextp , prevf=prevf , nextf=nextf)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    #giving the result of first searched slug
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/skills")
def skills():
    return render_template('skills.html', params=params)

@app.route("/work")
def work():
    return render_template('work.html', params=params)

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        #Inserting Data into DB
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        msg = request.form.get('msg')
        entry = Contact(cname=name, cemail = email, csubject=subject, cmsg = msg, date= datetime.now())
        db.session.add(entry)
        db.session.commit()
        #Flask-mail(Sending Mail)
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients = [params['gmail-user']],
                          body = subject + "\n" + msg
                          )
    return render_template('contact.html', params=params)

@app.route("/edit/<string:id>", methods = ['GET', 'POST'])
def edit(id):
    #only if user is already logged in
    if('user' in session and session['user'] == params['admin_user']):
        if(request.method=='POST'):
            title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            date = datetime.now()
            #to add post
            if id == '0':
                post = Post(title = title , tagline = tagline , slug = slug, content = content, date=date)
                db.session.add(post)
                db.session.commit()
                return redirect('/edit/'+ id)
            #to edit post
            else:
                post = Post.query.filter_by(id = id).first()
                post.title = title
                post.tagline = tagline
                post.slug = slug 
                post.content = content
                post.date = date
                db.session.commit()
                return redirect('/edit/'+ id)
        #giving result of post according to id
        post = Post.query.filter_by(id = id).first()
        return render_template('edit.html', params=params , post=post, id=id)  
    
@app.route("/feedback", methods = ['GET', 'POST'])
def feedback():
    if(request.method=='POST'):
        #Inserting Data into DB
        name = request.form.get('name')
        email = request.form.get('email')
        msg = request.form.get('msg')
        img = request.files['img']
        #uploading file
        img.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(img.filename)))
        feed = Feedback(name=name, email = email, feedback = msg, img = img, date= datetime.now())
        db.session.add(feed)
        db.session.commit()
    return render_template('index.html', params=params)    

@app.route("/logout")
def logout():
    #Killing The Session
    session.pop('user')
    return redirect('/dashboard')
    
@app.route("/delete/<string:id>", methods = ['GET', 'POST'])
def delete(id):
    #only if user is already logged in
    if('user' in session and session['user'] == params['admin_user']):
        post = Post.query.filter_by(id = id).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')
        
    

#running app in 5000(defualt) port
app.run(debug=True)