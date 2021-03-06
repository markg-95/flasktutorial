from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login, app
from hashlib import md5
from time import time
import jwt


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

        The object returned is a SQLAlchemy query object.
        When calling this function, we should immediately call a method like
        all() or first() to get a list of the objects we expect returned.

        ex. from '/index' route:
        posts = current_user.followed_posts().all()
        """
        just_followed_posts = Post.query.join(
        followers, (followers.c.followed_id==Post.user_id)).filter(
        followers.c.follower_id==self.id)
        own_posts = Post.query.filter_by(user_id=self.id)
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
        return 'https://www.gravatar.com/avatar/%s?d=identicon&s=%d' % (md5(self.email.encode('utf-8')).hexdigest(), size)

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
        return self.followed.filter(followers.c.followed_id==user.id).count() > 0

    # Resetting passwords
    def get_reset_password_token(self, expires_in=600):
        """
        jwts are JSON Web Tokens.
        >>> token = jwt.encode(payload_dict, SECRET_KEY, algorithm='HS256')
        >>> jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        payload_dict

        our payload_dict will look like:
        {'reset_password': user_id, 'exp': token_expiration}


        """

        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

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
