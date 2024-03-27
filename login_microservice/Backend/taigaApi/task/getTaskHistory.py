import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import asyncio

from taigaApi.utils.asyncAPIs import build_and_execute_apis


# Load environment variables from .env file
load_dotenv()


# Function to retrieve task history and calculate cycle time for closed tasks
def get_task_history(tasks, auth_token):

    # Get Taiga API URL from environment variables
    taiga_url = os.getenv('TAIGA_URL')

    # Define headers including the authorization token and content type
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }

    task_ids = (lambda : [task['id'] for task in tasks if 'id' in task])()
    task_history_url = f"{taiga_url}/history/task/"
    tasks_history = asyncio.run(build_and_execute_apis(task_ids, task_history_url, headers))
    return tasks_history


# Function to extract the date when a task transitioned from 'New' to 'In progress'
def extract_new_to_in_progress_date(history_data):
    for event in history_data:
        values_diff = event.get("values_diff", {})
        if "status" in values_diff and values_diff["status"] == ["New", "In progress"]:
            created_at = datetime.fromisoformat(event["created_at"])
            return created_at
    return None

def calculate_cycle_times_for_tasks(tasks, auth_token):
    tasks_map = (lambda: {task['id']: (task, None) for task in tasks})()
    tasks_history = get_task_history(tasks, auth_token)
    for task_history in tasks_history:
        task_id = int(task_history[0]['key'].split(':')[1])
        tasks_map[task_id] = (tasks_map[task_id][0], task_history)
    # Iterate over each task to retrieve task history and calculate cycle time
    result = []
    for task in list(tasks_map.values()):
        cycle_time = 0
        finished_date = task[0]["finished_date"]
        history_data = task[1]

        # Extract the date when the task transitioned from 'New' to 'In progress'
        in_progress_date = extract_new_to_in_progress_date(history_data)

        # Convert finished_date and in_progress_date to datetime objects
        finished_date = datetime.fromisoformat(finished_date[:-1])
        if in_progress_date:
            in_progress_date = datetime.fromisoformat(str(in_progress_date)[:-6])
            cycle_time = (finished_date - in_progress_date).days + (
                        finished_date - in_progress_date).seconds / 86400
        result.append({
            "task_id": task[0]['ref'],
            "cycle_time": cycle_time
        })
    return result