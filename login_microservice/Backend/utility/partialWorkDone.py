from datetime import datetime, timedelta
from taigaApi.milestones.getMilestonesForSprint import get_milestones_by_sprint
from taigaApi.task.getTasks import get_tasks

def partialWorkDone(project_id, sprint_id, auth_token, result_store = None, key = None):
    # Fetching milestones / usertories from taiga endpoint
    milestone = get_milestones_by_sprint(project_id, sprint_id, auth_token)

    # Fetching tasks from taiga endpoint
    tasks = get_tasks(project_id, auth_token)

    # Data required to plot is stored here
    processing_user_stories = {}

    data_to_plot = {
        "total_story_points": 0,
        "x_axis": [],
        "y_axis": [],
        "ideal_projection": [],
        "actual_projection": [],
        "sprint_start_date": milestone["estimated_start"],
        "sprint_end_date": milestone["estimated_finish"],
        "sprint_id": sprint_id
    }

    for user_story in milestone["user_stories"]:
        if user_story["total_points"] == None:
            continue

        processing_user_stories[user_story["id"]] = {
            "points": int(user_story["total_points"]),
            "created_date": user_story["created_date"],
            "finish_date": user_story["finish_date"],
            "tasks": [],
        }
        data_to_plot["total_story_points"] += int(user_story["total_points"])

    start_date = datetime.strptime(data_to_plot["sprint_start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(data_to_plot["sprint_end_date"], "%Y-%m-%d")

    data_to_plot["x_axis"] = [
        (start_date + timedelta(days=day)).strftime("%d %b %Y")
        for day in range((end_date - start_date).days + 1)
    ]
    data_to_plot["y_axis"] = [
        i for i in range(0, data_to_plot["total_story_points"] + 20, 10)
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

    for task in tasks:
        if task["user_story"] not in processing_user_stories:
            continue

        task_finished_date = None
        if task["status_extra_info"]["is_closed"]:
            task_finished_date = datetime.fromisoformat(
                task["finished_date"]
            ).strftime("%d %b %Y")

        processing_user_stories[task["user_story"]]["tasks"].append(
            {
                "closed": task["status_extra_info"]["is_closed"],
                "finished_date": task_finished_date,
            }
        )

    for index in range(0, len(data_to_plot["x_axis"])):
        current_processing_date = data_to_plot["x_axis"][index]
        current_processing_date_points = 0

        if index <= 0:
            current_processing_date_points = data_to_plot["total_story_points"]
        else:
            current_processing_date_points = data_to_plot["actual_projection"][
                index - 1
            ]

        for user_story_id in processing_user_stories:
            user_story = processing_user_stories[user_story_id]
            task_count = len(user_story["tasks"])

            if task_count <= 0:
                continue

            task_points = user_story["points"] / task_count

            for task in user_story["tasks"]:
                if (
                    not task["closed"]
                    or task["finished_date"] != current_processing_date
                ):
                    continue

                current_processing_date_points = (
                    current_processing_date_points - task_points
                )

        data_to_plot["actual_projection"].append(
            round(current_processing_date_points, 1)
        )

    if result_store != None and key != None:
        result_store[key]['partial_work_done'] = data_to_plot

    return data_to_plot