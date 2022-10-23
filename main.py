import requests
import redis
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
from io import BytesIO


storage = redis.Redis(
    host='localhost',
    port=6379
    )

submissions_key_prefix = "_submissions"
solved_key_prefix = "_solved"

usernames = ['mapc_me']

leetcode_url = "https://leetcode.com/graphql"
leetcode_user_statistic_graphql_query = """
query getUserProfile($username: String!) {
    matchedUser(username: $username) {
        submitStats { 
            totalSubmissionNum {        
                difficulty        
                count        
                submissions      
            }    
        }  
    }
}
"""


def run_user_statistic_query(username):
    variables = {'username': username}
    request = requests.post(leetcode_url, json={'query': leetcode_user_statistic_graphql_query , 'variables': variables})
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(f"Unexpected status code returned: {request.status_code}")

def get_hard(response_json):
    
    return response_json['data']['matchedUser']['submitStats']['totalSubmissionNum'][3]["count"]

def get_medium(response_json):
    return response_json['data']['matchedUser']['submitStats']['totalSubmissionNum'][2]["count"]


def get_easy(response_json):
    return response_json['data']['matchedUser']['submitStats']['totalSubmissionNum'][1]["count"]


def get_submissions(response_json):
    return response_json['data']['matchedUser']['submitStats']['totalSubmissionNum'][0]["count"]


def get_user_data_today():
    users_statistic = {}
    for username in usernames:
        has_data = storage.exists(username)
        current_user_statistic = [0, 0, 0, 0]
        last_user_statistic = []
        if has_data:
            last_user_statistic = json.loads(storage.get(username).decode('utf-8'))
        
        response_json = run_user_statistic_query(username)

        if has_data:
            current_user_statistic[0] = get_easy(response_json) - last_user_statistic[0]
            current_user_statistic[1] = get_medium(response_json) - last_user_statistic[1]
            current_user_statistic[2] = get_easy(response_json) - last_user_statistic[2]
            current_user_statistic[3] = get_submissions(response_json) - last_user_statistic[3]
        
        storage.set(username, json.dumps(current_user_statistic))
        users_statistic[username] = current_user_statistic
    
    return users_statistic

def create_stat_table(users_statistic):
    fig, ax = plt.subplots()
    fig.patch.set_visible(False)
    ax.axis('off')
    ax.axis('tight')

    data=[]
    for username, stat in users_statistic.items():
        user_data = []
        user_data.append(username)
        for s in stat:
            user_data.append(s)
        data.append(user_data)

    df = pd.DataFrame(data,columns=["username", "easy", "medium", "hard", "sumbissions"])

    ax.table(cellText=df.values, colLabels=df.columns, loc='center')
    ax.set_title("Users statistic " + datetime.today().strftime('%Y-%m-%d'))
    fig.tight_layout()

    return fig
    # plt.savefig(ax.get_title())

def send_to_telegram(fig):
    api_token = ''
    chat_id = -1001508628054
    apiURL = f'https://api.telegram.org/bot{api_token}/sendPhoto'

    plot_file = BytesIO()
    fig.savefig(plot_file, format='png')
    plot_file.seek(0)

    request_data = {
        "chat_id": chat_id,
        "plot_file": plot_file,
    }

    params = {'chat_id': request_data['chat_id']}
    files = {'photo': request_data['plot_file']}

    resp = requests.post(apiURL, data = params, files = files)
    print(resp.text)

data = get_user_data_today()
fig = create_stat_table(data)
send_to_telegram(fig)
