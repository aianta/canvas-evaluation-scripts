import json
import pprint

TASKS_PATH = "sample_generated_data/10-course-pack-oct-6-2025/tasks.json"

def read_tasks(path):
    with open(f'{path}', 'r') as f:
        output = json.load(f)
    return output

tasks = read_tasks(TASKS_PATH)

odobotNL_tasks = []

for index, task in enumerate(tasks):
    print(f"Task {index}")

    for i_index, instance in enumerate(task['instances']):
        print(f"Instance {i_index}")

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
                "userLocation": "http://localhost:8088",
                "task": ques_value
            }
        }

        odobotNL_tasks.append(odobotNL_task)

with open("odoBotNL_tasks.json", "w") as f:
    f.write(f"{json.dumps(odobotNL_tasks)}")