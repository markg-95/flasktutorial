from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5


# followers is an auxillary table that exhibits a many-to-many relationship.
# auxillary tables in SQL terms typically store only foreign keys, which is
# why we don't construct it as a Model subclass.
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
    )

class User(UserMixin, db.Model):
    """
    Class for our blog's users. It extends UserMixin and db.Model.

    UserMixin: from flask_login takes care of loggin users in and out, as well as
    keeping refference of the user through their unique user ID. an ID will be
    known if the user is authenticated.
    db.Model objects layout the structure of an item in a database.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)


    '''
    implementing followers
    the following relationship implements this idea:
    A follows B. A is the left User. B is the right User.
    If we query A, we get the list of users followed by A.

    Below,
    • 'User' is the user followed by A.
    • secondary is the aux. table above this class.
    • primary join is the condition that links A to B.
        - the follower id matches self.id (first var. in this class above)
    • secondaryjoin links B to A. B is the followed user, so they have the
      same id.
    • backref

    '''
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')


    def followed_posts(self):
        """
        Query the data base for all posts from the followed users
        of a user.

        Below, we are joining the Post table with the aux. followers table.
        From that table, we filter by which the followed user == Post.user_id.
        Then, we want to include (union in) our own posts into the timeline.
        So we find our posts and union them with the followed posts.
        Finally, we order by descending order of timestamp.

        """
        just_followed_posts = Post.query.join(
        followers, (followers.c.followed_id==Post.user_id)).filter(
        followers.c.follower_id==self.id)
        own_posts = Post.query.filter(user_id==self.id)
        return just_followed_posts.union(own_posts).order_by(Post.timestamp.desc())

    def __repr__(self):
        """
        This dictates how a User object is printed.
        """
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        '''
        Gravatar is an avatar generating service.
        Below we are encoding the lower-cased email as bytes and requesting an avatar
        from gravatar.
        '''
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?=identicon&s={}'.format(digest, size)

    '''
    Implement following and unfollowing other users.
    '''
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
    def is_following(self, user):
        return self.followed(filter(followers.c.followerd_id==user.id)).count() > 0

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)
