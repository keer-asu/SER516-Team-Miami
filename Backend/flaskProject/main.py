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
app.secret_key = secrets.token_hex(16)

@app.route("/", methods=["GET", "POST"])
def loginPage():
    if "auth_token" in session:
        return redirect("/slug-input")

    if request.method == "POST":
        micro_login_response = requests.post(
            "http://login_microservice:5000/login",
            data = request.form
        )

        if micro_login_response.status_code == 200:
            session["auth_token"] = micro_login_response.json()["auth_token"]
            return redirect("/slug-input")
        else:
            return render_template("login2.html", error=True)

    return render_template("login2.html", error=False)


@app.route("/logout", methods=["GET"])
def log_out():
    if "auth_token" in session:
        del session["auth_token"]

    return redirect("/")


@app.route("/slug-input", methods=["GET", "POST"])
def slug_input():
    if "auth_token" not in session:
        return redirect("/")

    if request.method == "POST":
        project_slug = request.form["slugInput"]
        project_info = get_project_by_slug(project_slug, session["auth_token"])

        if project_info == None:
            return render_template("slug-input.html", error=True)

        if "sprint_mapping" in session:
            del session["sprint_mapping"]

        if "total_sprints" in session:
            del session["total_sprints"]

        session["project_id"] = project_info["id"]

        return redirect("/sprint-selection")

    return render_template("slug-input.html")


@app.route("/sprint-selection", methods=["GET", "POST"])
def sprint_selection():
    if "auth_token" not in session:
        return redirect("/")

    if "project_id" not in session:
        return redirect("/slug-input")

    if "sprint_mapping" not in session or "total_sprints" not in session:
        sprintMapping, total_sprints = get_number_of_milestones(session["project_id"], session["auth_token"])
        session["sprint_mapping"] = sprintMapping
        session["total_sprints"] = total_sprints

    if request.method == "POST":
        session["sprint_selected"] = request.form.get("selectionOption")

        # TODO: Bug fix (sprint mapping)
        session["sprint_id"] = session["sprint_mapping"][
            str(len(session["sprint_mapping"]) - int(request.form.get("selectionOption")) + 1)
        ]

        return redirect("/metric-selection")

    return render_template("sprint-selection.html", total_sprints=session["total_sprints"])


@app.route('/burndown-graph', methods=['GET'])
def burndown_graph():
    if "auth_token" not in session:
        return redirect("/")

    if "sprint_selected" not in session:
        return redirect("/sprint-selection")

    if "metric_selected" not in session:
        return redirect("/metric-selection")

    return render_template("burndown-graph.html")


@app.route("/<user_story>/get-business-value", methods=["GET"])
def get_business_value_by_user_story(user_story):
    if "auth_token" not in session:
        return redirect("/")
    auth_token = session["auth_token"]
    project_id = session["project_id"]
    taiga_url = os.getenv("TAIGA_URL")
    # business_value_id = get_business_value_id(project_id, auth_token)
    business_value_id = 0
    business_value_api_url = (
        f"{taiga_url}/userstories/custom-attributes-values/{user_story}"
    )
    # Define headers including the authorization token and content type
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }
    try:
        # Make a GET request to Taiga API to retrieve user stories
        response = requests.get(business_value_api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        # Extracting information from the response
        business_value_res = response.json()
        if str(business_value_id) not in business_value_res["attributes_values"]:
            business_value_res["attributes_values"][str(business_value_id)] = 0
        return business_value_res["attributes_values"][str(business_value_id)]
    except requests.exceptions.RequestException as e:
        # Handle errors during the API request and print an error message
        print(f"Error fetching project by slug: {e}")

        return redirect('/error')


@app.route('/lead-time-graph', methods=['GET'])
def lead_time_graph():
    if "auth_token" not in session:
        return redirect("/")
    auth_token = session["auth_token"]
    project_id = session["project_id"]
    sprint_id = session["sprint_id"]
    form_data = {
        "auth_token" : auth_token,
        "project_id" : project_id,
        "sprint_id" : sprint_id
    }
    leadtime_response = requests.get(
        "http://leadtime_microservice:5000/lead-time-graph",
        data=form_data
    )
    lead_times_for_sprint = leadtime_response.json()["lead_times_for_sprint"]
    return render_template(
        "lead-time-sprint-graph.html", lead_times_for_sprint=lead_times_for_sprint
    )


@app.route("/cycle-time-graph", methods=["GET"])
def cycle_time_graph_get():
    if "auth_token" not in session:
        return redirect("/")
    # show users all the closed tasks in the selected sprint

    closed_tasks_in_a_spirnt = get_closed_tasks_for_a_sprint(
        session["project_id"], session["sprint_id"], session["auth_token"]
    )
    session["closed_tasks_in_a_sprint"] = closed_tasks_in_a_spirnt

    in_sprint_ids = [task["ref"] for task in closed_tasks_in_a_spirnt]
    return render_template("CycleTimeGraph.html", closed_tasks=in_sprint_ids)


# fetch data and calculate cycle time of tasks or user stories selected and display graph.
# This is not average cycle time.
@app.route("/cycle-time-graph", methods=["POST"])
def cycle_time_graph():
    if "auth_token" not in session:
        return redirect("/")
    if request.method == "POST":
        closed_tasks_ids = request.json["closed_tasks_ids"]
        response = requests.post('http://microservice_cycle_time:5000/cycle_time_calculation', json = {'session': dict(session), 'closed_tasks_ids': closed_tasks_ids})
        if response.content:
            result = response.json()
        else:
            result = {}
        return jsonify(result)
        
@app.route("/partial-work-done-chart", methods=["GET"])
def partial_work_done_chart():
    # If user is not log`ged in redirect to login page
    if "auth_token" not in session:
        return redirect("/")

    # Fetching the auth token from session
    auth_token = session["auth_token"]

    if "project_id" in session:
        project_id = session["project_id"]

    if "sprint_id" in session:
        sprint_id = session["sprint_id"]

    # Throwing error if the user has submitted project_id or sprint_id
    if (not project_id) or (not sprint_id):
        return "Invalid request!"
    
    res = requests.get(f"http://partial_work_done:5000/{project_id}/{sprint_id}/{auth_token}/partial-work-done-chart")

    if(res.status_code == 500):
        return redirect('/error')

    return jsonify(res.json()["data_to_plot"]), res.status_code

@app.route("/total-work-done-chart", methods=["GET"])
def total_work_done_chart():
    # If user is not log`ged in redirect to login page
    if "auth_token" not in session:
        return redirect("/")

    # Fetching the auth token from session
    auth_token = session["auth_token"]

    # TODO: Bug fix (redirect)
    if "project_id" in session:
        project_id = session["project_id"]

    if "sprint_id" in session:
        sprint_id = session["sprint_id"]

    # Throwing error if the user has submitted project_id or sprint_id
    if (not project_id) or (not sprint_id):
        return "Invalid request!"

    res = requests.get(f"http://total_work_done:5000/{project_id}/{sprint_id}/{auth_token}/total-work-done-chart")

    if(res.status_code == 500):
        return redirect('/error')

    return jsonify(res.json()["data_to_plot"]), res.status_code


@app.route("/burndown-bv")
def render_burndown_bv():
    if "auth_token" not in session:
        return redirect("/")
    return render_template("burndown-bv.html")


@app.route("/burndown-bv-data", methods=["GET"])
def burndown_bv_microservice():
    try:
        microservice_response = requests.get(
            "http://burndown_bv_microservice:5000/burndown-bv-data",
            data={
                "project_id": session["project_id"],
                "sprint_id": session["sprint_id"],
                "auth_token": session["auth_token"],
            },
        )
        return microservice_response.json()

    except Exception as e:
        print(e)
        return redirect("/error")


@app.route("/work-auc")
def render_work_auc():
    if "auth_token" not in session:
        return redirect("/")
    return render_template("work-auc.html")


@app.route("/work-auc-data", methods=["GET"])
def work_auc_microservice():
    if "auth_token" not in session:
        return redirect("/")
    # if request.method == "GET":
    try:
        microservice_response = requests.get(
            "http://work_auc_microservice:5000/work-auc-data",
            data={
                "project_id": session["project_id"],
                "auth_token": session["auth_token"],
            },
        )
        return microservice_response.json()

    except Exception as e:
        print(e)
        return redirect("/error")


@app.route("/error", methods=["GET"])
def render_error():
    return render_template("error.html")


@app.route("/VIP", methods=["GET"])
def render_VIP_page():
    if "auth_token" not in session:
        return redirect("/")
    return render_template("ValueInProgressGraph.html")


@app.route("/VIPC", methods=["GET"])
def calculate_VIP():
    if "auth_token" not in session:
        return redirect("/")
    # get all the user stories from the sprint
    response = requests.post('http://microservice_vip:5000/VIPC', json = {'session': dict(session)})
    data_points = response.json()
    return jsonify(data_points)


@app.route("/business-value-auc", methods=["GET", "POST"])
def get_business_value_auc_delta():
    if request.method == "GET":
        sprintMapping, sprints = get_number_of_milestones(
            session["project_id"], session["auth_token"]
        )
        auc_map = dict()
        sprint_bv_auc_delta = None
        for sprint_id in list(sprintMapping.values()):
            running_bv_data, ideal_bv_data = get_business_value_data_for_sprint(
                session["project_id"], sprint_id, session["auth_token"]
            )
            total_bv_for_sprint = list(ideal_bv_data.values())[0]
            if total_bv_for_sprint:
                bv_auc_delta = (
                    lambda: {
                        item: round(
                            abs(
                                (total_bv_for_sprint - running_bv_data[item])
                                / total_bv_for_sprint
                                - (total_bv_for_sprint - ideal_bv_data[item])
                                / total_bv_for_sprint
                            ),
                            2,
                        )
                        for item in running_bv_data.keys()
                    }
                )()
                if sprint_id == session["sprint_id"]:
                    sprint_bv_auc_delta = bv_auc_delta
                auc_map[sprint_id] = sum(list(bv_auc_delta.values()))
            else:
                auc_map[sprint_id] = 0
        auc = dict()
        for item in sprintMapping.items():
            auc["Sprint " + str(sprints - int(item[0]) + 1)] = auc_map[item[1]] * 100
        auc_list = list(auc.items())

        auc_list.sort(key = lambda x : x[0])
        return render_template('value-auc-graph.html', bv_auc_delta=list(sprint_bv_auc_delta.items()), auc = auc_list)


@app.route("/metric-selection", methods=["GET", "POST"])
def metric_selection():
    if "auth_token" not in session:
        return redirect("/")

    if request.method == "POST":
        session["metric_selected"] = request.form.get("selectionOption")
        if session["metric_selected"] == "burndown":
            return redirect("/burndown-graph")


        elif session["metric_selected"] == "cycle_time":
            return redirect("/cycle-time-graph")

        elif session["metric_selected"] == "lead_time":
            return redirect("/lead-time-graph")

        elif session["metric_selected"] == "Work_AUC":
            return redirect("/work-auc")

        elif session["metric_selected"] == "lead_time":
            return redirect("/lead-time-graph")

        elif session["metric_selected"] == "VIP":
            return redirect("/VIP")

        elif session['metric_selected'] == 'BD_Consistency':
            return redirect('/bd-view')

        elif session["metric_selected"] == "Value_AUC":
            return redirect("/business-value-auc")

        elif session["metric_selected"] == "multiple_bd":
            return redirect("/multiple-bd")

        elif session["metric_selected"] == "multisprint_bd":
            return redirect("/multi-sprint-bd")

        elif session["metric_selected"] == "arbitrary_lead_time":
            return redirect("/arbitrary-lead-time")

    return render_template("metric-selection.html")


@app.route("/bd-view", methods=["GET"])
def render_bd_page():
    if "auth_token" not in session:
        return redirect('/')

    if 'project_id' not in session:
        return redirect('/slug-input')

    if 'sprint_id' not in session:
        return redirect('/sprint-selection')
    
    res = requests.get("http://bd_consistency:5000/render-bd-view")

    if(res.status_code == 500):
        return redirect('/error')

    return res.text, res.status_code


@app.route("/bd-calculation", methods=["GET"])
def bd_calculations():
    if "auth_token" not in session:
        return redirect('/')

    if 'project_id' in session:
        project_id = session['project_id']

    if 'sprint_id' in session:
        sprint_id = session['sprint_id']

    if((not project_id) or (not sprint_id)):
        return 'Invalid request!'
    
    auth_token = session["auth_token"]
    
    res = requests.get(f"http://bd_consistency:5000/{project_id}/{sprint_id}/{auth_token}/bd-calculation")

    if(res.status_code == 500):
        return redirect('/error')

    return jsonify(res.json()["data_to_plot"]), res.status_code

        
    #data needs for calculation
    #running_bv_data, ideal_bv_data, data_to_plot["actual_projection"], data_to_plot["totla_story_points"]


@app.route("/multiple-bd", methods=["GET"])
def render_multiple_bd_page():
    if "auth_token" not in session:
        return redirect('/')

    if 'project_id' not in session:
        return redirect('/slug-input')

    if 'sprint_id' not in session:
        return redirect('/sprint-selection')

    return render_template("multiple-bd.html")


@app.route("/multi-sprint-bd", methods=["GET"])
def render_mult_sprint_bd_page():
    if "auth_token" not in session:
        return redirect('/')
    if 'project_id' not in session:
        return redirect('/slug-input')
    project_id = session["project_id"]
    auth_token = session["auth_token"]
    res = requests.post(f"http://multi_sprint_burndown:5000/{project_id}/{auth_token}/multi-sprint-bd", json={"sprint_mapping": session["sprint_mapping"]})
    if(res.status_code == 500):
        return redirect('/error')
    return res.text, res.status_code

@app.route("/arbitrary-lead-time", methods=["GET", "POST"])
def get_arbitrary_lead_time():
    if "auth_token" not in session:
        return redirect('/')

    if 'project_id' not in session:
        return redirect('/slug-input')

    if request.method == 'GET' and request.args.get('start_date'):
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        lead_times_for_timeframe = get_lead_times_for_arbitrary_timeframe(project_id=session['project_id'], start_time=start_date, end_time=end_date, auth_token=session['auth_token'])
        return render_template(
            "arbitrary-lead-time.html", lead_times_for_timeframe=lead_times_for_timeframe,
            is_data_calculated = True)

    elif request.method == 'GET':
        return render_template("arbitrary-lead-time.html", lead_times_for_timeframe= None, is_data_calculated = False)
