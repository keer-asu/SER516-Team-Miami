import sqlite3
import time
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
from datetime import datetime, timedelta

from taigaApi.authenticate import authenticate
from taigaApi.project.getProjectBySlug import get_project_by_slug
from taigaApi.project.getProjectTaskStatusName import get_project_task_status_name
from taigaApi.userStory.getUserStory import get_user_story
from taigaApi.task.getTaskHistory import calculate_cycle_times_for_tasks
from taigaApi.task.getTasks import (
    get_closed_tasks,
    get_all_tasks,
    get_one_closed_task,
    get_tasks,
    get_closed_tasks_for_a_sprint,
    get_lead_times_for_arbitrary_timeframe
)
from taigaApi.project.getProjectMilestones import (
    get_number_of_milestones,
    get_milestone_id,
)

from taigaApi.milestones.getMilestonesForSprint import (
    get_milestones_by_sprint,
    get_milestone_stats_by_sprint,
)
from taigaApi.task.getTasks import (
    get_lead_times_for_tasks,
    get_userstories_for_milestones,
)
from taigaApi.customAttributes.getCustomAttributes import (
    get_business_value_data_for_sprint,
    get_business_value_id,
    get_user_story_business_value_map,
    get_custom_attribute_values,
)
from taigaApi.userStory.getUserStory import get_user_story_start_date

from utility.partialWorkDone import partialWorkDone
from utility.totalWorkDone import totalWorkDone

import secrets
import requests
from threading import Thread

app = Flask(__name__)

@app.route("/login", methods=["POST"])
def loginPage():
    username = request.form["username"]
    password = request.form["password"]
    auth_token = authenticate(username, password)
    if auth_token:
        return jsonify({"auth_token": auth_token}), 200
    else:
        "failed to authenticate", 401


