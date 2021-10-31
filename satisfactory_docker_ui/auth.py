from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField
)
from wtforms.validators import DataRequired
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    current_app,
    flash
)
from flask_login import login_user, logout_user

from satisfactory_docker_ui.classes.alchemy import User, get_session

auth = Blueprint(
    'auth',
    __name__,
    template_folder='templates'
)


class LoginForm(FlaskForm):
    username = StringField(label="Username", validators=[DataRequired()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    remember_me = BooleanField()


@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    username = form.username.data
    password = form.password.data

    if form.validate_on_submit():
        Session = get_session()
        session = Session()
        user = session.query(User).filter_by(name=username).first()
        if user and user.verify_password(password):
            login_user(user)
            return redirect(url_for("root"))
        else:
            current_app.logger.error("Invalid login!")
            flash("Invalid login!")
    else:
        print(form.errors)

    return render_template("login.html", form=form)


@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("root"))
