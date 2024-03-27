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
    lead_times_for_sprint = get_lead_times_for_tasks(project_id, sprint_id, auth_token)
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
        # The data should be sent by fetch and POST method in JSON format

        #Check if the database exists and if the database still valid
        database_name = 'sprint_{}_project_{}.db'.format(session["sprint_id"], session["project_id"])
        database_path = os.path.join(app.root_path, database_name)

        if os.path.exists(database_path):
            current_time = time.time()
            creation_time = os.path.getctime(database_path)
            difference = (current_time - creation_time) / 60
            if difference <= 30:
                #retrieve data from
                result = []
                conn = sqlite3.connect(database_path)
                c = conn.cursor()
                c.execute('SELECT * FROM cycle_times')
                entries = c.fetchall()
                result = [{'task_id': entry[0], 'cycle_time': entry[1]} for entry in entries]
                return jsonify(result)

        else:
            #create database
            conn = sqlite3.connect(database_path)
            c = conn.cursor()
            closed_tasks_ids = request.json["closed_tasks_ids"]

            closed_tasks_selected = []
            if closed_tasks_ids == [0]:
                closed_tasks_selected = session["closed_tasks_in_a_sprint"]
            else:
                closed_tasks_selected = [
                    task
                    for task in session["closed_tasks_in_a_sprint"]
                    if task["ref"] in closed_tasks_ids
                ]

            # fetch data from taiga api
            if closed_tasks_selected != None:

                result = calculate_cycle_times_for_tasks(
                    closed_tasks_selected, session["auth_token"]
                )
                c.execute('''
                    CREATE TABLE IF NOT EXISTS cycle_times (
                        id TEXT PRIMARY KEY,
                        cycle_time REAL NOT NULL
                        )
                    ''')
                for entry in result:
                    c.execute('INSERT INTO cycle_times (id, cycle_time) VALUES (?, ?)', (entry['task_id'], entry['cycle_time']))
                conn.commit()
                conn.close()
                return jsonify(
                    result
                )
            conn.commit()
            conn.close()


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

    try:
        data_to_plot = partialWorkDone(project_id, sprint_id, auth_token)

        return json.dumps(data_to_plot)
    except Exception as e:
        # Handle errors during the API request and print an error message
        print(e)
        return redirect("/error")

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

    try:
        data_to_plot = totalWorkDone(project_id, sprint_id, auth_token)

        return json.dumps(data_to_plot)
    except Exception as e:
        # Handle errors during the API request and print an error message
        print(e)
        return redirect("/error")


@app.route("/burndown-bv")
def render_burndown_bv():
    if "auth_token" not in session:
        return redirect("/")
    return render_template("burndown-bv.html")


@app.route("/burndown-bv-data", methods=["GET", "POST"])
def get_burndown_bv_data():
    if request.method == "GET":
        running_bv_data, ideal_bv_data = get_business_value_data_for_sprint(
            session["project_id"], session["sprint_id"], session["auth_token"]
        )
        return list((list(running_bv_data.items()), list(ideal_bv_data.items())))


@app.route("/work-auc")
def render_work_auc():
    if "auth_token" not in session:
        return redirect("/")
    return render_template("work-auc.html")


@app.route("/work-auc-data", methods=["GET", "POST"])
def get_work_auc_data():
    if request.method == "GET":
        try:
            sprintMapping, sprints = get_number_of_milestones(
                session["project_id"], session["auth_token"]
            )

            work_auc_by_sprint_id = {}
            for sprint_id in list(sprintMapping.values()):
                milestone = get_milestones_by_sprint(
                    session["project_id"], sprint_id, session["auth_token"]
                )

                data_to_plot = {
                    "total_story_points": 0,
                    "x_axis": [],
                    "y_axis": [],
                    "ideal_projection": [],
                    "actual_projection": [],
                    "sprint_start_date": milestone["estimated_start"],
                    "sprint_end_date": milestone["estimated_finish"],
                }

                for user_story in milestone["user_stories"]:
                    if user_story["total_points"] == None:
                        continue
                    data_to_plot["total_story_points"] += int(
                        user_story["total_points"]
                    )

                start_date = datetime.strptime(
                    data_to_plot["sprint_start_date"], "%Y-%m-%d"
                )
                end_date = datetime.strptime(
                    data_to_plot["sprint_end_date"], "%Y-%m-%d"
                )

                data_to_plot["x_axis"] = [
                    (start_date + timedelta(days=day)).strftime("%d %b %Y")
                    for day in range((end_date - start_date).days + 1)
                ]
                data_to_plot["y_axis"] = [
                    i for i in range(0, data_to_plot["total_story_points"] + 20, 20)
                ]

                ideal_graph_points = data_to_plot["total_story_points"]
                avg_comp_story_point = data_to_plot["total_story_points"] / (
                    len(data_to_plot["x_axis"]) - 1
                )
                while ideal_graph_points > 0:
                    temp = round(ideal_graph_points - avg_comp_story_point, 1)
                    if len(data_to_plot["ideal_projection"]) <= 0:
                        data_to_plot["ideal_projection"].append(
                            data_to_plot["total_story_points"]
                        )
                    if temp > 0:
                        data_to_plot["ideal_projection"].append(temp)
                    else:
                        data_to_plot["ideal_projection"].append(0)
                    ideal_graph_points = temp
                for index in range(0, len(data_to_plot["x_axis"])):
                    current_processing_date = data_to_plot["x_axis"][index]
                    current_processing_date_points = 0
                    if index <= 0:
                        current_processing_date_points = data_to_plot[
                            "total_story_points"
                        ]
                    else:
                        current_processing_date_points = data_to_plot[
                            "actual_projection"
                        ][index - 1]
                    total_points_completed = 0
                    for user_story in milestone["user_stories"]:
                        if (
                            user_story["finish_date"] == None
                            or user_story["total_points"] == None
                        ):
                            continue
                        finish_date = datetime.fromisoformat(
                            user_story["finish_date"]
                        ).strftime("%d %b %Y")

                        if finish_date != current_processing_date:
                            continue
                        total_points_completed = (
                            user_story["total_points"] + total_points_completed
                        )
                    data_to_plot["actual_projection"].append(
                        round(
                            current_processing_date_points - total_points_completed, 1
                        )
                    )

                actual_value = data_to_plot["actual_projection"]
                ideal_value = data_to_plot["ideal_projection"]
                total_points = data_to_plot["total_story_points"]
                work_auc_delta = []
                for idx in range(len(actual_value)):
                    if total_points != 0:
                        work_auc_delta.append(
                            round(
                                abs(
                                    (total_points - actual_value[idx]) / total_points
                                    - (total_points - ideal_value[idx]) / total_points
                                ),
                                2,
                            )
                        )
                    else:
                        work_auc_delta.append(0)

                work_auc_by_sprint_id[sprint_id] = sum(work_auc_delta) * 100

            work_auc_by_sprint_order = []
            for sprint_id in list(sprintMapping.values()):
                work_auc_by_sprint_order.insert(0, work_auc_by_sprint_id[sprint_id])

            sprint_label = []
            for i in range(sprints):
                sprint_label.append("Sprint " + str(i + 1))

            return jsonify(
                {
                    "x_axis": sprint_label,
                    "work_auc_by_sprint_order": work_auc_by_sprint_order,
                }
            )

        except Exception as e:
            # Handle errors during the API request and print an error message
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
    user_stories = get_userstories_for_milestones(
        [session["sprint_id"]], session["auth_token"]
    )[
        0
    ]  # it has complete infromation

    # get business value of each user story, and calculate total business value
    get_userstory_ids = lambda: [userstory["id"] for userstory in user_stories]
    userstory_ids = get_userstory_ids()
    business_value_id = get_business_value_id(
        session["project_id"], session["auth_token"]
    )
    custom_attribute_values = get_custom_attribute_values(
        userstory_ids, session["auth_token"]
    )
    ###
    user_story_business_value_map = get_user_story_business_value_map(
        business_value_id, custom_attribute_values
    )
    total_business_value = sum(user_story_business_value_map.values())
    ###

    # get total user stories points

    ####
    total_points = 0
    story_points_map = {}
    story_finish_date_map = {}
    ####

    for story in user_stories:
        if story["total_points"] != None:
            total_points += story["total_points"]
            story_points_map[story["id"]] = story["total_points"]
            story_finish_date_map[story["id"]] = story["finish_date"]

    # get story start dates
    ###
    story_start_date_map = get_user_story_start_date(
        user_stories, session["auth_token"]
    )
    ###

    # get starting date of a sprint
    # get ending date of a sprint "finish_date"
    sprint_data = get_milestones_by_sprint(
        session["project_id"], session["sprint_id"], session["auth_token"]
    )
    sprint_start_date = sprint_data["estimated_start"]
    sprint_start_date = datetime.fromisoformat(sprint_start_date)
    sprint_finish_date = sprint_data["estimated_finish"]
    sprint_finish_date = datetime.fromisoformat(sprint_finish_date)
    # check which user stories is in progress at a given date
    date_list = [
        (sprint_start_date + timedelta(days=day))
        for day in range((sprint_finish_date - sprint_start_date).days + 1)
    ]
    data_points = []
    one_day_points = 0
    one_day_BV = 0
    for date in date_list:
        date = date.replace(tzinfo=None)
        for user_story in user_stories:
            if story_start_date_map[user_story["id"]] == None:
                continue
            start_date = story_start_date_map[user_story["id"]].replace(tzinfo=None)
            if story_finish_date_map[user_story["id"]] != None:
                finish_date = datetime.fromisoformat(
                    story_finish_date_map[user_story["id"]]
                ).replace(tzinfo=None)
            else:
                finish_date = None


            if start_date.date() <= date.date() and (finish_date == None or finish_date.date() > date.date()):

                one_day_points += story_points_map[user_story["id"]]
                one_day_BV += user_story_business_value_map[user_story["id"]]

        data_points.append(
            {
                "date": date.strftime("%d %b %Y"),
                "user_story_points": one_day_points / total_points,
                "BV": one_day_BV / total_business_value,
            }
        )
        one_day_points = 0
        one_day_BV = 0

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

    return render_template("metric-selection.html")


@app.route("/bd-view", methods=["GET"])
def render_bd_page():
    if "auth_token" not in session:
        return redirect('/')

    if 'project_id' not in session:
        return redirect('/slug-input')

    if 'sprint_id' not in session:
        return redirect('/sprint-selection')

    return render_template("BD-Consistency-graph.html")


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
    
    # Data required to plot is stored here
    data_to_plot = { 
            "total_story_points": 0,
            "x_axis": [],
            "bv_projection": [],
            "story_points_projection": []
    }

    milestone = get_milestones_by_sprint(project_id, sprint_id, session["auth_token"])

    for user_story in milestone["user_stories"]:
        if user_story["total_points"] == None: 
            continue

        data_to_plot["total_story_points"] += int(user_story["total_points"])
            
    start_date  = datetime.strptime(milestone["estimated_start"], '%Y-%m-%d')
    end_date = datetime.strptime(milestone["estimated_finish"], '%Y-%m-%d')

    data_to_plot["x_axis"] = [(start_date + timedelta(days=day)).strftime("%d %b %Y") for day in range((end_date - start_date).days + 1)]

    for index in range(0, len(data_to_plot["x_axis"])):
        current_processing_date = data_to_plot["x_axis"][index]
        current_processing_date_points = 0

        if index <= 0:
            current_processing_date_points = data_to_plot["total_story_points"]
        else:
            current_processing_date_points = data_to_plot["story_points_projection"][index - 1]

        total_points_completed = 0
        for user_story in milestone["user_stories"]:
            if(user_story["finish_date"] == None or user_story["total_points"] == None):
                continue

            finish_date = datetime.fromisoformat(user_story["finish_date"]).strftime("%d %b %Y")
                    
            if(finish_date != current_processing_date):
                continue

            total_points_completed = user_story["total_points"] + total_points_completed

        data_to_plot["story_points_projection"].append(round(current_processing_date_points - total_points_completed, 1))

    running_bv_data, _ = get_business_value_data_for_sprint(session['project_id'], session['sprint_id'], session['auth_token'])
    data_to_plot['bv_projection'] = running_bv_data

    return json.dumps(data_to_plot)

        
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

    project_id = session['project_id']
    auth_token = session['auth_token']
    data_to_plot = {}
    threads = []

    for key in session["sprint_mapping"].keys():
        sprintId = session["sprint_mapping"][key]
        sprint_key = len(session["sprint_mapping"]) - int(key) + 1
        data_to_plot[sprint_key] = {}

        # partial work done
        thread1 = Thread(target=partialWorkDone, args=(project_id, sprintId, auth_token, data_to_plot, sprint_key))

        # total work done
        thread2 = Thread(target=totalWorkDone, args=(project_id, sprintId, auth_token, data_to_plot, sprint_key))

        # business value
        thread3 = Thread(target=get_business_value_data_for_sprint, args=(project_id, sprintId, auth_token, data_to_plot, sprint_key))

        thread1.start()
        thread2.start()
        thread3.start()
        threads.append(thread1)
        threads.append(thread2)
        threads.append(thread3)

    for thread in threads:
        thread.join()


    print(json.dumps(data_to_plot, indent=4))

    return render_template("multi-sprint-bd.html", data_to_plot=data_to_plot)

@app.route("/arbitrary-lead-time", methods=["GET", "POST"])
def get_arbitrary_lead_time():
    # start_date = request.args.get('start_date')
    # end_date = request.args.get('end_date')
    lead_times_for_timeframe = get_lead_times_for_arbitrary_timeframe(project_id=session['project_id'], start_time='2024-02-04', end_time='2024-02-21', auth_token=session['auth_token'])
    return render_template(
        "arbitrary-lead-time.html", lead_times_for_timeframe=lead_times_for_timeframe
    )