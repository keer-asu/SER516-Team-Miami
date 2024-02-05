from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import getpass
import json
from datetime import datetime, timedelta
from taigaApi.authenticate import authenticate
from taigaApi.project.getProjectBySlug import get_project_by_slug
from taigaApi.project.getProjectTaskStatusName import get_project_task_status_name
from taigaApi.userStory.getUserStory import get_user_story
from taigaApi.task.getTaskHistory import get_task_history
from taigaApi.task.getTasks import get_closed_tasks, get_all_tasks
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


# @app.route("/")
# def index():
#     return render_template("index.html")


@app.route("/")
def index():
    return render_template("index.html", error=False)


@app.route("/login", methods=["GET", "POST"])
def loginPage():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        auth_token = authenticate(username, password)
        if auth_token:
            session["auth_token"] = auth_token
            return jsonify(
                {
                    "status": "success",
                    "username": username,
                    "password": password,
                    "auth_token": auth_token,
                }
            )
        else:
            session["auth_token"] = None
            return jsonify(
                {
                    "status": "failure",
                    "auth_token": auth_token,
                    "username": username,
                    "password": password,
                }
            )
