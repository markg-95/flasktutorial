from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from app.email import send_password_reset_email
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post
from werkzeug.urls import url_parse
from datetime import datetime

'''
This file contains our app\'s view functions.
These are functions that get mapped to URLs.
They update the contents of html pages when we call render_template(...).
'''


@app.before_request
def before_request():
	"""
	Update models.User's last_seen field in app.db.
	@app.before_request ensures this function gets called
	before the other view functions.
	"""
	if current_user.is_authenticated:
		current_user.last_seen = datetime.utcnow()
		db.session.commit()

# home page
@app.route('/', methods=['GET','POST'])
@app.route('/index', methods=['GET','POST'])
@login_required # decorator used by Flask-Login to ensure a user must be logged in to view this page
def index():
	# making a post
	form=PostForm()
	if form.validate_on_submit():
		post = Post(body=form.post.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		flash('Your post is now live!')
		return redirect(url_for('index'))
		"""
		The reason why we're redirecting back to this page is to follow the
		post/redirect/get pattern.
		After making a 'post' request, we should redirect always. This prevents
		confusing / unexpected behaviour such as a user refreshing a page and
		the most recent post request being made twice, prompting a warning message. Redirecting
		The redirect forces a 'get' request, thwarting the duplicate-post issue.

		Pagination: This involves querying for and generating a subset of all
		values of interest from the data base. (i.e. Don't display 1,000,000
		posts, display the latest 20.)
		paginate(page #, # of values to get, True if you want error, False if
		you want [])
		From the above query object, .items returns the list of elements.
		Below, we see other helpful uses in determining whether there are more
		pages to display.
		"""
	page = request.args.get('page', 1, type=int)
	posts = current_user.followed_posts().paginate(
		page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('index', page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('index', page=posts.prev_num) \
		if posts.has_prev else None
	return render_template('index.html', title='Home', form=form,
		posts=posts.items, next_url=next_url,
		prev_url=prev_url)

# explore page
@app.route('/explore')
@login_required
def explore():
	"""
	Renders the index.html template. On this page we see posts from all users
	so that users can discover new users.
	For details on pagination, see 'index()' above.
	"""
	page = request.args.get('page', 1, type=int)
	posts = current_user.followed_posts().paginate(
		page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('index', page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('index', page=posts.prev_num) \
		if posts.has_prev else None
	return render_template('index.html', title='Home',
		posts=posts.items, next_url=next_url,
		prev_url=prev_url)

# login page
@app.route('/login', methods=['GET','POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash('Invalid username or password.')
			return redirect(url_for('login'))
		login_user(user, remember=form.remember_me.data)
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			'''
			note: the above second conditional ensures that all
			url's are relative (no outside agent can slip in a url path).
			'''
			next_page = url_for('index')
		return redirect(next_page)
	return render_template('login.html', title='Sign In', form=form)

# log out and return to home page
@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))

# register new user page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
		# user is already authenticated. return to index page.
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

# reset password request page
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = ResetPasswordRequestForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user:
			send_password_reset_email(user)
		flash('Check your email for the instructions to reset your password')
		return redirect(url_for('login'))
	return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

# reset password page
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
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

# user profile page
@app.route('/user/<username>')
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get('page', 1, type=int) #query string, default, type
	posts = user.posts.order_by(Post.timestamp.desc()).paginate(
		page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('user', username=user.username, page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('user', username=user.username, page=posts.prev_num) \
	if posts.has_prev else None
	'''
	note, above we use url_for to pass extra arguments.
	username specifies the user whose profile page we're targetting.
	the page argument is used in this function to determine which of
	this user's posts should be displayed (pagination).

	below, if we're viewing someone else's profile, form serves as the
	follow/unfollow button.
	'''
	form = EmptyForm()
	return render_template('user.html',user=user,posts=posts.items,form=form)

from app.forms import EditProfileForm

# edit profile page
@app.route('/edit_profile', methods=['GET', 'POST'])
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

# following and unfollowing users
@app.route('/follow/<username>', methods=['POST'])
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

@app.route('/unfollow/<username>', methods=['POST'])
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

@app.route('/break_app')
def break_app():
	return None
