import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()


# Function to retrieve user stories for a specific project from the Taiga API
def get_user_story(project_id, auth_token):

    # Get Taiga API URL from environment variables
    taiga_url = os.getenv('TAIGA_URL')

    # Construct the URL for the user stories API endpoint for the specified project
    user_story_api_url = f"{taiga_url}/userstories?project={project_id}"

    # Define headers including the authorization token and content type
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }

    try:

        # Make a GET request to Taiga API to retrieve user stories
        response = requests.get(user_story_api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        # Extract and return the user stories information from the response
        project_info = response.json()
        return project_info

    except requests.exceptions.RequestException as e:

        # Handle errors during the API request and print an error message
        print(f"Error fetching project by slug: {e}")
        return None

# Filter out the user stories that are in progress
def get_in_progress_user_stories(project_id, auth_token):
    user_stories = get_user_story(project_id, auth_token)
    in_progress_stories = []
    for story in user_stories:
        if story["status_extra_info"]["name"] == "In progress":
            in_progress_stories.append(story)
    return in_progress_stories

# get business value custom attribute id
def get_business_value_id(project_id, auth_token):
    taiga_url = os.getenv('TAIGA_URL')
    custom_attribute_api_url = f"{taiga_url}/userstory-custom-attributes?project={project_id}"
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.get(custom_attribute_api_url, headers=headers)
        response.raise_for_status() 

        custome_attributes = response.json()
        for attribute in custome_attributes:
            if attribute["name"] == "BV":
                return attribute["id"]
        return None

    except requests.exceptions.RequestException as e:

        # Handle errors during the API request and print an error message
        print(f"Error fetching custom attributes: {e}")
        return None

# Function to retrieve user story start date
def get_user_story_start_date(stories, auth_token):

    # Get Taiga API URL from environment variables
    taiga_url = os.getenv('TAIGA_URL')

    # Define headers including the authorization token and content type
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }
    result = {}
    # Iterate over each task to retrieve task history and calculate cycle time
    for story in stories:
        story_history_url = f"{taiga_url}/history/userstory/{story['id']}"
        try:
            # Make a GET request to Taiga API to retrieve story history
            response = requests.get(story_history_url, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            history_data = response.json()

            # Extract the date when the story transitioned from 'New' to 'In progress'
            in_progress_date = extract_new_to_in_progress_date(history_data)
            print(in_progress_date)
            result[story["id"]] = in_progress_date
 
        except requests.exceptions.RequestException as e:
            # Handle errors during the API request and print an error message
            print(f"Error fetching project by slug: {e}")

    return result

# Function to extract the date when a user story transitioned from 'New' to 'In progress'
def extract_new_to_in_progress_date(history_data):
    for event in history_data:
        values_diff = event.get("values_diff", {})
        if "status" in values_diff and values_diff["status"] == ["New", "In progress"]:
            created_at = datetime.fromisoformat(event["created_at"])
            return created_at
    return None
