import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # ...
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'localhost'
    MAIL_PORT = 8025
    MAIL_USE_TLS = None

    MAIL_DO_AUTH = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    ADMINS = ['monroe.jeffw@gmail.com']

    BLOG_SHOW_OTHERS = False

    LANGUAGES = ['en', 'es']

# Pagination
    POSTS_PER_PAGE = 5
