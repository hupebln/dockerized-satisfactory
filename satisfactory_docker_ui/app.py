import os
import logging

from flask import render_template, request
from flask_login import login_required, LoginManager
from docker import from_env

from satisfactory_docker_ui import app
from satisfactory_docker_ui.auth import auth
from satisfactory_docker_ui.classes.alchemy import get_session, User, ensure_admin_user

logger = logging.getLogger(__name__)

docker_client = from_env()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

if not os.getenv("FLASK_SECRET"):
    raise Exception("No secret for flask found")

if not ensure_admin_user():
    app.logger.error("admin user not present")

app.secret_key = os.getenv("FLASK_SECRET")
app.template_folder = "templates"
app.static_folder = "static"
app.register_blueprint(blueprint=auth, url_prefix='/auth')


@login_manager.user_loader
def load_user(user_id):
    Session = get_session()
    session = Session()
    
    try:
        user = session.query(User).get(user_id)
    finally:
        session.close()

    return user


@app.route("/", methods=["GET"])
@login_required
def root():
    server_name = os.getenv("HOSTNAME_SERVER")
    server = docker_client.containers.get(server_name)
    logs = server.logs(timestamps=True, tail=50)
    decoded_logs = logs.decode()
    logs_list = decoded_logs.split("\n")

    return render_template(
        "root.html",
        container_info=server.attrs,
        logs=logs_list
    )


@app.route("/actions", methods=["POST"])
@login_required
def actions():
    action = request.form.get("action")
    if action:
        server_name = os.getenv("HOSTNAME_SERVER")
        server = docker_client.containers.get(server_name)
        action_mapping = {
            "restart": server.restart,
            "stop": server.stop,
            "start": server.start
        }
        _do = action_mapping.get(action)
        _do()
        app.logger.info("ACTION TRIGGERED: %s", action)

    return ""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
