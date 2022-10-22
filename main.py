from collections import UserDict
import requests
import redis


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

def get_user_submissions(response_json):
    grouped_submissions = response_json['data']['matchedUser']['submitStats']['totalSubmissionNum']
    count = 0
    for group in grouped_submissions:
        count = group['submissions']
        break
    return count

def get_user_tasks_statistic(response_json):
    grouped_submissions = response_json['data']['matchedUser']['submitStats']['totalSubmissionNum']
    count = 0
    for group in grouped_submissions:
        count = group['count']
        break
    return count

def get_submissions_today():
    submissions_daily_statistic = {}
    for username in usernames:
        response_json = run_user_statistic_query(username)
        user_submissions = get_user_submissions(response_json)

        storage_key = username + submissions_key_prefix
        
        if not storage.exists(storage_key):
            submissions_daily_statistic[username] = 0
        else:
            currentSubmissions = int(storage.get(storage_key))
            submissions_daily_statistic[username] = user_submissions - currentSubmissions
        
        storage.set(storage_key, user_submissions)

    return submissions_daily_statistic


def get_solved_tasks_today():
    solved_tasks_daily_statistic = {}
    for username in usernames:
        response_json = run_user_statistic_query(username)
        user_solved_tasks = get_user_tasks_statistic(response_json)

        storage_key = username + solved_key_prefix
        
        if not storage.exists(storage_key):
            solved_tasks_daily_statistic[username] = 0
        else:
            currentSolved = int(storage.get(storage_key))
            solved_tasks_daily_statistic[username] = user_solved_tasks - currentSolved
        
        storage.set(storage_key, user_solved_tasks)

    return solved_tasks_daily_statistic



print(get_submissions_today())
print(get_solved_tasks_today())
