from flask import render_template
from webapp import db
from . import bp


@bp.app_errorhandler(404)
def not_found_error(*_):
    print('custom error handler: 404')
    return render_template('404.html'), 404


@bp.app_errorhandler(500)
def internal_error(*_):
    db.session.rollback()
    return render_template('500.html'), 500
