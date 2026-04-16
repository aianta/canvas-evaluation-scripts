import json
import pprint
import random



TASKS_PATH = "sample_generated_data/odox-7c-mar-12-2026/tasks.json"
CHOSEN_TASKS_PATH = "odoBotNL_tasks.json"
OUTPUT_JSONL = "webvoyager_tasks_full_71.jsonl"
'''
Prepares output from data generation scripts into format appropriate for web voyager execution. 
'''

def read_tasks(path):
    with open(f'{path}', 'r') as f:
        output = json.load(f)
    return output

tasks = read_tasks(TASKS_PATH)
chosen_tasks = read_tasks(CHOSEN_TASKS_PATH)
chosen_tasks = [x['odoBotNL']['id'] for x in chosen_tasks]


web_voyager_tasks = []

for index,task in enumerate(tasks):
    print(f"Task {index}")

    # randomly pick one instance per task
    instance = random.choice(task['instances'])

    prefix = f"Use the username: {instance["instance_username"]} and password: {instance["instance_password"]} to login to Canvas.\n"

    suffix = None

    if task["type"] == "Information Seeking":
        #continue # TODO: Currently skipping information seeking tasks.

        if "answer_type" not in task:
            print(f"{task}")

        if task["answer_type"] == 'Date Time':
            suffix = '''
Write your answer in the following format:

Answer: YYYY-MM-DD HH:mm'''

        elif task["answer_type"] == 'Numeric':
            suffix = '''
Write your answer in the following format:

Answer: [Number]'''

        elif task["answer_type"] == 'Text':
            suffix = """
Write your answer in the following format:

Answer: '[Text]'"""

        else:
            print(f"Unknown answer_type {task["answer_type"]}") 

    ques_value = f"{prefix}{instance["instance_text"]}{"" if suffix is None else suffix}"

    web_voyager_task = {
        "web": "http://localhost:8088",
        "web_name": "Canvas LMS",
        "description": f"Instance of task {task['id']}",
        "id": f"{instance['id']}",
        "ques": ques_value
    }

    #if instance['id'] in chosen_tasks:
    web_voyager_tasks.append(web_voyager_task)

with open(OUTPUT_JSONL, "w") as f:
    for t in web_voyager_tasks:
        f.write(f"{json.dumps(t)}\n")
    