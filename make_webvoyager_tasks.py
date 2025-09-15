import json
import pprint

'''
Prepares output from data generation scripts into format appropriate for web voyager execution. 
'''

def read_tasks(path):
    with open(f'{path}', 'r') as f:
        output = json.load(f)
    return output

tasks = read_tasks("tasks.json")

web_voyager_tasks = []

for index,task in enumerate(tasks):
    print(f"Task {index}")



    for i_index, instance in enumerate(task["instances"]):
        print(f"Instance {i_index}")

        prefix = "Use the username: sammy@ualberta.ca and password: op3TPfE3J5MK to login to Canvas.\n"

        suffix = None

        if task["type"] == "Information Seeking":

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

        web_voyager_tasks.append(web_voyager_task)

with open("webvoyager_tasks.jsonl", "w") as f:
    for t in web_voyager_tasks:
        f.write(f"{json.dumps(t)}\n")
    