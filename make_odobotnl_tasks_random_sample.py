import json
import pprint
import csv
import random

TASKS_PATH = "sample_generated_data/odox-7c-mar-12-2026/tasks_2032.json"
TRAINING_TASKS_PATH = "odoBotNL_tasks_doable.json"
OUTPUT_JSON = "odoBotNL_tasks_2032.json"
OUTPUT_CSV = "odoBotNL_task_table_2032.csv"

def read_tasks(path):
    with open(f'{path}', 'r') as f:
        output = json.load(f)
    return output

tasks = read_tasks(TASKS_PATH)
training_tasks = read_tasks(TRAINING_TASKS_PATH)
training_tasks = [x["odoBotNL"]["id"] for x in training_tasks]

odobotNL_tasks = []

odobotNL_tasks_csv = []
odobotNL_tasks_csv.append(["Task ID","Eval ID", "Task"])

for index, task in enumerate(tasks):
    print(f"Task {index}")

    # randomly pick one instance per task
    instance = random.choice(task['instances'])
    # while instance['id'] in training_tasks:
    #     instance = random.choice(task['instances']) 

    prefix = f"Use the username: {instance["instance_username"]} and password: {instance["instance_password"]} to login to Canvas.\n"

    suffix = None

    if task["type"] == "Information Seeking":
        continue # TODO: Currently skipping information seeking tasks.

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

    odobotNL_task = {
        "odoBotNL": {
            "id": f"{instance['id']}",
            "_evalId": f"{index + 1}|OdoBotNL|{instance['id']}",
            "userLocation": "http://localhost:8088/login/canvas",
            "task": ques_value
        }
    }


    odobotNL_tasks.append(odobotNL_task)
    odobotNL_tasks_csv.append([instance['id'], f"{index + 1}|OdoBotNL|{instance['id']}", ques_value])

print(f"{len(odobotNL_tasks)} odobotNL tasks ready")

with open(OUTPUT_JSON, "w") as f:
    f.write(f"{json.dumps(odobotNL_tasks)}")

with open(OUTPUT_CSV, "w") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(odobotNL_tasks_csv)