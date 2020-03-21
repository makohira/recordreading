from flask import session, render_template
from functools import wraps

appdir = 'recordreading'
def check_logged_in(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'logged_in' in session:
            return func(*args, **kwargs)
        return render_template('login.html', the_title='読書記録', app_dir=appdir)
    return wrapper
