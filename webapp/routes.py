from webapp import db, webapp
from flask import render_template, flash, redirect, url_for, request
from webapp.forms import LoginForm, RegistrationForm, EditProfileForm, \
    EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm

from flask_login import logout_user, current_user, login_user, login_required
from webapp.models import User, Post
from werkzeug.urls import url_parse
from datetime import datetime
from webapp.email import send_password_reset_email
from flask_babel import _

def get_page_others():
    page = request.args.get('page', 1, type=int)
    c_others = "yes" if webapp.config['BLOG_SHOW_OTHERS'] else "yes"
    others = request.args.get('others', c_others, type=str)

    if others == "yes":
        max_pages = round(0.5 + current_user.followed_posts().count() / webapp.config['POSTS_PER_PAGE'])
        if page > max_pages:
            page = max_pages
        posts = current_user.followed_posts().paginate(page=page,
                                                       per_page=webapp.config['POSTS_PER_PAGE'],
                                                       error_out=False)
    elif others == "all":
        max_pages = round(0.5 + Post.query.count() / webapp.config['POSTS_PER_PAGE'])
        if page > max_pages:
            page = max_pages
        posts = Post.query.order_by(Post.timestamp.desc()).paginate(page=page,
                                                       per_page=webapp.config['POSTS_PER_PAGE'],
                                                       error_out=False)
    else:
        max_pages = round( 0.5 + current_user.user_posts().count() / webapp.config['POSTS_PER_PAGE'])
        if page > max_pages:
            page = max_pages
        posts = current_user.user_posts().paginate(page=page,
                                                   per_page=webapp.config['POSTS_PER_PAGE'],
                                                   error_out=False)
    return [page, others, max_pages, posts ]

@webapp.route('/', methods=['GET', 'POST'])
@webapp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()

    print("form =", id(form), id(form.post))
    print(f"post.data = {form.post.data}")
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('index'))

    page, others, max_pages, posts = get_page_others()

    return render_template("index.html",
                           title='Home Page',
                           form=form,
                           # check=check,
                           page=page,
                           posts=posts,
                           others=others,
                           max_pages = max_pages)

@webapp.route('/explore')
@login_required
def explore():

    page, others, max_pages, posts = get_page_others()
    return render_template('index.html',
                           title='Explore',
                           posts=posts,
                           page=page,
                           others="all",
                           max_pages=max_pages)


@webapp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        print("login <args>:", request.args.get('next'))
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@webapp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@webapp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@webapp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()

    page, others, max_pages, posts = get_page_others()
    form = EmptyForm()
    return render_template('user.html',
                           user=user,
                           posts=posts,
                           page = page,
                           max_pages = max_pages,
                           form=form)

@webapp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@webapp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)
@webapp.route('/user_list')
@login_required
def user_list():
    users = User.query.all()

    return render_template('user_list.html', users=users)

@webapp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@webapp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@webapp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        print("   looking for user")
        if user:
            print("    found user")
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@webapp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@webapp.route('/post_table', methods=['GET'])
@login_required
def get_post_table():
    print('Chilling in get_post table')
    page, others, max_pages, posts = get_page_others()
    print(f'    in python: others={others}, page={page}')
    html = render_template('_post_table.html', posts=posts)

    ret_val = { 'html' : html,
                'max_pages': max_pages }

    return ret_val
