from flask import Flask, render_template, request, Response
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message
from sqlalchemy import  create_engine
from sqlalchemy.sql import select
from project.models.database import init_db, db_session, engine
from project.models.models import Contact, Data
from project import application
import project.controllers.stream_controller
from tempfile import gettempdir


# configure session to use filesystem (instead of signed cookies)
application.config["SESSION_FILE_DIR"] = gettempdir()
application.config["SESSION_PERMANENT"] = False
application.config["SESSION_TYPE"] = "filesystem"
Session(application)

# avoid ddos attack
limiter = Limiter(
    application,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)


@application.teardown_appcontext
def shutdown_session(exception=None):
	db_session.remove()


# ensure responses aren't cached
if application.config["DEBUG"]:
    @application.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response


def contact():
    if request.method == 'POST':
        # save into db
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # check if empty
        # temporary: will add email format checking
        if not (name and email and message):
            return

        u = Contact(name, email, message)
        db_session.add(u)
        db_session.commit()

        # gmail service
        # bad way, but in order to avoid showing password and account
        # manually put data to Blog.db everytime when deploying
        conn = engine.connect()
        s = select([Data])
        result = conn.execute(s)
        row = result.fetchone()
        conn.close()
        application.config.update(
            DEBUG=True,
            #EMAIL SETTINGS
            MAIL_SERVER='smtp.gmail.com',
            MAIL_PORT=465,
            MAIL_USE_SSL=True,
            MAIL_USERNAME = row['mail_username'],
            MAIL_PASSWORD = row['mail_password']
            )
        mail=Mail(application)

        msg = Message( 'Reminder from blog',
                    sender='remindvictorlee@gmail.com',
                    recipients= ['hellovictorlee@gmail.com'])
        msg.body =  "NAME: " + name + "\nMESS: " + message + "\nMAIL: " + email
        mail.send(msg)


@application.route('/', methods=['GET', 'POST'])
def index():
    try:
        contact()
        return render_template('index.html')
    except Exception:
        return "error!!"


@application.route('/blog', methods=['GET', 'POST'])
def blog():
    try:
        contact()
        return render_template('blog.html')
    except Exception:
        return "error!!"


@application.route('/tutorial', methods=['GET', 'POST'])
@application.route('/tutorial/<page>', methods=['GET', 'POST'])
def tutorial(page=''):
    try:
        contact()
        if any(page):
            return render_template('tutorial/' + page + '.html')
        else:
            return render_template('tutorial.html')
    except Exception:
        return "error!!"


@application.route('/video', methods=['GET', 'POST'])
def video():
    try:
        contact()
        return render_template('video.html')
    except Exception:
        return "error!!"


@application.route('/resume', methods=['GET', 'POST'])
def resume():
    try:
        contact()
        return render_template('resume.html')
    except Exception:
        return "error!!"
