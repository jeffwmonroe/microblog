from flask import Flask, request
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
import os
from flask_babel import Babel

print('webapp ... initializing')
webapp = Flask(__name__)
webapp.config.from_object(Config)


bootstrap = Bootstrap(webapp)
mail = Mail(webapp)
moment = Moment(webapp)
babel = Babel(webapp)

login = LoginManager(webapp)
login.login_view = 'auth.login'

db = SQLAlchemy(webapp)
migrate = Migrate(webapp, db)

if not webapp.debug:
    print("Webapp is not in debug mode")

    webapp.config['MAIL_SERVER'] = 'localhost'
    print("MAIL_SERVER", webapp.config['MAIL_SERVER'])
    if webapp.config['MAIL_SERVER']:
        print("configuring the email server ...")
        auth = None
        if webapp.config['MAIL_DO_AUTH']:
            print('trying to do auth')
            if webapp.config['MAIL_USERNAME'] or webapp.config['MAIL_PASSWORD']:
                auth = (webapp.config['MAIL_USERNAME'], webapp.config['MAIL_PASSWORD'])
                print("   auth was successful")
        secure = None
        if webapp.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(  mailhost=(webapp.config['MAIL_SERVER'], webapp.config['MAIL_PORT']),
                                     fromaddr='no-reply@' + webapp.config['MAIL_SERVER'],
                                     toaddrs=webapp.config['ADMINS'], subject='Microblog Failure',
                                     credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        webapp.logger.addHandler(mail_handler)

if not webapp.debug:
    # ...

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    webapp.logger.addHandler(file_handler)

    webapp.logger.setLevel(logging.INFO)
    webapp.logger.info('Microblog startup')

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match( webapp.config['LANGUAGES'])

from webapp.errors import bp as errors_bp
webapp.register_blueprint(errors_bp)

from webapp.auth import bp as auth_bp
webapp.register_blueprint(auth_bp, url_prefix='/auth')

from . import routes, models



