import os
from datetime import timedelta, datetime

import requests
from dotenv import load_dotenv
from taigaApi.task.getTasks import get_userstories_for_milestones
from taigaApi.milestones.getMilestonesForSprint import get_milestone_stats_by_sprint
import asyncio
from taigaApi.utils.asyncAPIs import build_and_execute_apis

# Load environment variables from a .env file
load_dotenv()

def get_business_value_id(project_id, auth_token):
    # Get Taiga API URL from environment variables
    taiga_url = os.getenv('TAIGA_URL')

    # Construct the URL for the user story custom attributes API endpoint for the project
    user_story_custom_attributes_api_url = f"{taiga_url}/userstory-custom-attributes?project={project_id}"

    # Define headers including the authorization token and content type
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }

    try:

        # Make a GET request to Taiga API to retrieve custom attributes
        response = requests.get(user_story_custom_attributes_api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        # return business value
        custom_attributes = response.json()
        get_business_value_id = lambda custom_attributes:\
            next(custom_attribute['id'] for custom_attribute in custom_attributes if custom_attribute['name'] == 'BV')
        return get_business_value_id(custom_attributes)

    except requests.exceptions.RequestException as e:

        # Handle errors during the API request and print an error message
        print(f"Error fetching tasks: {e}")
        return None

# Gets the ideal and actual Business value delivered for sprint
def get_business_value_data_for_sprint(project_id, sprint_id, auth_token, result_store = None, key = None):
    business_value_id = get_business_value_id(project_id, auth_token)
    user_stories = get_userstories_for_milestones([sprint_id], auth_token)[0]
    get_userstory_ids = lambda: [userstory['id'] for userstory in user_stories]
    userstory_ids = get_userstory_ids()
    custom_attribute_values = get_custom_attribute_values(userstory_ids, auth_token)
    milestone_stats = get_milestone_stats_by_sprint(sprint_id, auth_token)
    sprint_days = (lambda : [day['day'] for day in milestone_stats['days']])()
    running_bv_data, ideal_bv_data = build_business_value_data(user_stories, custom_attribute_values, business_value_id, sprint_days)

    if result_store != None and key != None:
        result_store[key]['business_value'] = running_bv_data

    return running_bv_data, ideal_bv_data

# Builds the ideal and actual business value data objects
def build_business_value_data(user_stories, custom_attribute_values, business_value_id, sprint_days):
    user_story_business_value_map = get_user_story_business_value_map(business_value_id, custom_attribute_values)
    total_business_value = sum(user_story_business_value_map.values())
    business_value_data_map = dict((x, 0) for x in sprint_days)
    for user_story in user_stories:
        if user_story['is_closed'] :
            finish_date = datetime.fromisoformat(user_story['finish_date']).strftime('%Y-%m-%d')
            if finish_date in sprint_days:
                business_value_data_map[finish_date] -= user_story_business_value_map[user_story['id']]
    running_bv = total_business_value
    for item in business_value_data_map.items():
        business_value_data_map[item[0]] +=running_bv
        running_bv = business_value_data_map[item[0]]
    running_business_value_data = dict()
    for item in business_value_data_map.keys():
        running_business_value_data[datetime.strptime(item, "%Y-%m-%d").strftime("%b-%d")] = business_value_data_map[item]
    delta_bv_per_day = total_business_value/(len(sprint_days) -1)
    ideal_business_value_data = (lambda : { item : total_business_value for item in running_business_value_data})()
    i = 0
    for item in ideal_business_value_data:
        ideal_business_value_data[item]  =  round(ideal_business_value_data[item] - delta_bv_per_day*i, 2)
        i+=1
    return running_business_value_data, ideal_business_value_data


# Fetches the custom attribute values for list of user stories
def get_custom_attribute_values(user_stories, auth_token):
    taiga_url = os.getenv('TAIGA_URL')

    user_story_custom_attributes_value_api_url = f"{taiga_url}/userstories/custom-attributes-values/"

    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }
    result = asyncio.run(
        build_and_execute_apis(user_stories, user_story_custom_attributes_value_api_url, headers))
    return result

# Generates a map of user story and business value
def get_user_story_business_value_map(business_value_id, custom_attribute_values):
    user_story_business_value_map = dict()
    for custom_attribute in custom_attribute_values:
        if str(business_value_id) in custom_attribute['attributes_values']:
            user_story_business_value_map[custom_attribute['user_story']] = int(custom_attribute['attributes_values'][str(business_value_id)])
        else :
            user_story_business_value_map[custom_attribute['user_story']] = 0
    return user_story_business_value_map