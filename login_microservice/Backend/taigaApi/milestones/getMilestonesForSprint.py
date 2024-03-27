import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Function to retrieve user stories for a specific project from the Taiga API
def get_milestones_by_sprint(project_id, sprint_id, auth_token):

    # Get Taiga API URL from environment variables
    taiga_url = os.getenv('TAIGA_URL')

    # Construct the URL for the user stories API endpoint for the specified project
    milestones_api_url  = f"{taiga_url}/milestones/{sprint_id}?project={project_id}"

    # Define headers including the authorization token and content type
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }

    try:
        # Make a GET request to Taiga API to retrieve user stories
        mailstones_res = requests.get(milestones_api_url, headers=headers)
        mailstones_res.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        # Extracting information from the mailstones_res
        milestones = mailstones_res.json()

        return milestones
    except requests.exceptions.RequestException as e:

        # Handle errors during the API request and print an error message
        print(f"Error fetching milstones by sprint: {e}")
        return None

def get_milestone_stats_by_sprint(sprint_id, auth_token):

    # Get Taiga API URL from environment variables
    taiga_url = os.getenv('TAIGA_URL')

    # Construct the URL for the user stories API endpoint for the specified project
    milestones_api_url  = f"{taiga_url}/milestones/{sprint_id}/stats"

    # Define headers including the authorization token and content type
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }

    try:
        # Make a GET request to Taiga API to retrieve user stories
        milestone_stats_res = requests.get(milestones_api_url, headers=headers)
        milestone_stats_res.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        # Extracting information from the mailstones_res
        milestone_stats = milestone_stats_res.json()

        return milestone_stats
    except requests.exceptions.RequestException as e:

        # Handle errors during the API request and print an error message
        print(f"Error fetching milstones by sprint: {e}")
        return None
