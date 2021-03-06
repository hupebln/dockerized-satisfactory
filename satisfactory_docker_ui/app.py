import os
import glob
import logging

from flask import render_template, request, send_file, redirect, flash
from flask_login import login_required, LoginManager
from docker import from_env

from satisfactory_docker_ui import app
from satisfactory_docker_ui.auth import auth
from satisfactory_docker_ui.classes.alchemy import get_session, User, ensure_admin_user
from satisfactory_docker_ui.classes.savegame import SaveGameHeader

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


@app.route("/savegame", methods=["GET", "POST"])
@login_required
def savegame():
    savegame_path = os.getenv("SAVEGAME_PATH")

    list_files = [
        save_file
        for save_file in glob.glob(os.path.join(savegame_path, '*'))
        if os.path.isfile(save_file)
    ]

    latest_file = max(list_files, key=os.path.getmtime)
    app.logger.error(latest_file)

    if request.method == "GET":
        if not savegame_path:
            return "No SAVEGAME_PATH found", 501

        if not os.path.exists(savegame_path):
            return "Given path from SAVEGAME_PATH doesn't exist.", 501

        return send_file(latest_file, as_attachment=True, download_name="SaveGame.sav")

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect("/")
        file = request.files["file"]
        if file.filename == '':
            flash("No selected file")
            return redirect("/")

        uploaded_content = file.read()

        old_header = SaveGameHeader(save_file=latest_file)
        new_header = SaveGameHeader(save_bytes=uploaded_content)

        if not old_header.build_version == new_header.build_version:
            flash("Build version doesn't match")
            return redirect("/")

        if not old_header.session_name == new_header.session_name:
            flash("Session name doesn't match")
            return redirect("/")

        if file:
            with open(latest_file, 'wb') as latest_save_file:
                latest_save_file.write(uploaded_content)
            flash("file uploaded successfully")
            return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
