from webapp import db, webapp
from flask import render_template, flash, redirect, url_for, request
from webapp.main.forms import EditProfileForm, EmptyForm, PostForm

from flask_login import current_user, login_required
from webapp.models import User, Post

from datetime import datetime

from flask_babel import _
from webapp.main import bp

def get_page_list(user=None, others="yes", page=1):
    print("get_page_list:")
    print(f"   user={user}")
    print(f"   others={others}")
    print(f"   page={page}")

    if others == "all" or user is None:
        print("   user is None case!")
        max_pages = (Post.query.count() + webapp.config['POSTS_PER_PAGE'] - 1) // webapp.config['POSTS_PER_PAGE']
        if page > max_pages:
            page = max_pages
        posts = Post.query.order_by(Post.timestamp.desc()).paginate(page=page,
                                                                    per_page=webapp.config['POSTS_PER_PAGE'],
                                                                    error_out=False)
    elif others == "yes":
        print("   others = yes case")
        max_pages = (user.followed_posts().count() +
                     webapp.config['POSTS_PER_PAGE'] - 1) // webapp.config['POSTS_PER_PAGE']
        if page > max_pages:
            page = max_pages
        posts = user.followed_posts().paginate(page=page,
                                               per_page=webapp.config['POSTS_PER_PAGE'],
                                               error_out=False)
    else:
        print("   others = no case")
        max_pages = (user.user_posts().count() +
                     webapp.config['POSTS_PER_PAGE'] - 1) // webapp.config['POSTS_PER_PAGE']
        if page > max_pages:
            page = max_pages
        posts = user.user_posts().paginate(page=page,
                                           per_page=webapp.config['POSTS_PER_PAGE'],
                                           error_out=False)
    return [page, others, max_pages, posts]


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
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
        return redirect(url_for('main.index'))

    page, others, max_pages, posts = get_page_list(user=current_user,
                                                   others="yes",
                                                   page=1)

    print("right before render_template:")
    return render_template("index.html",
                           title='Home Page',
                           user=current_user,
                           form=form,
                           page=page,
                           posts=posts,
                           others=others,
                           max_pages=max_pages)


@bp.route('/explore')
@login_required
def explore():
    page, others, max_pages, posts = get_page_list(user=None,
                                                   others="all",
                                                   page=1)
    return render_template('index.html',
                           title='Explore',
                           posts=posts,
                           page=page,
                           others="all",
                           explore=True,
                           max_pages=max_pages)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()

    page, others, max_pages, posts = get_page_list(user=user,
                                                   others="no",
                                                   page=1)
    form = EmptyForm()
    return render_template('user.html',
                           user=user,
                           posts=posts,
                           page=page,
                           max_pages=max_pages,
                           form=form)


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@bp.route('/user_list')
@login_required
def user_list():
    users = User.query.all()

    return render_template('user_list.html', users=users)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/post_table', methods=['GET'])
@login_required
def get_post_table():
    print('Chilling in get_post table')
    page = request.args.get('page', 1, type=int)

    others = request.args.get('others', "yes", type=str)
    username = request.args.get('username', None, type=str)

    user = User.query.filter_by(username=username).first()
    print(f"   user={user}")
    page, others, max_pages, posts = get_page_list(user=user,
                                                   page=page,
                                                   others=others)
    print(f'    in python: others={others}, page={page}, max_pages = {max_pages}')
    html = render_template('_post_table.html', posts=posts)

    ret_val = {'html': html,
               'max_pages': max_pages}

    return ret_val
