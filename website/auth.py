from flask import Blueprint, render_template

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return "<p>Login</p>"

@auth.route('/logout')
def logout():
    return "<p>Logout</p>"

@auth.route('/sign-up')
def sign_up():
    return "<p>Sign Up</p>"


@auth.route('/sensors')
def sensors():
    return render_template("sensors.html")

@auth.route('/devices')
def devices():
    return render_template("devices.html")

@auth.route('/settings')
def settings():
    return render_template("settings.html")