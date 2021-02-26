from app import app, db
from app.models import User, Post, followers

@app.shell_context_processor
def make_shell_context():
    """
    This function is evoked when running 'flask shell' from the shell.
    It allows us to play with the database from the shell without
    having to import app.models.<model>.
    The keys in the dictionary that is returned are the strings we'll write in
    the shell when referencing our database models.
    """
    return {'db': db, 'User': User, 'Post': Post, 'followers': followers}
