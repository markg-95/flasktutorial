from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment

#

app = Flask(__name__) # our main application
app.config.from_object(Config) # config class stores our app's configuration variables.
db = SQLAlchemy(app) # SQL database
migrate = Migrate(app, db) # object for updating the database
login = LoginManager(app) # used for logging users in/out, password hashing, etc.
login.login_view = 'login' #
mail = Mail(app) # email support
bootstrap = Bootstrap(app) # bootstrap CSS framework
moment = Moment(app) # implements moment.js



from app import routes, models, errors

# Error handling
if not app.debug:
    """
    Send emails to admins when a bug occurs on the sight.
    """
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Microblog Failure',
            credentials=auth, secure=secure)

        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
    """
    Log errors to a file.
    """
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Microblog startup')
