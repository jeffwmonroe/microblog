from flask_mail import Message
from webapp import mail, webapp
from flask import render_template
from threading import Thread

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(webapp, msg)).start()

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_password_reset_email(user):
    print("    send_password_reset_email")
    token = user.get_reset_password_token()
    send_email('[Microblog] Reset Your Password',
               sender=webapp.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))
