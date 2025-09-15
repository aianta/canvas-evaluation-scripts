import json
import re
from datetime import datetime

'''
The task class contains the information about a task and its instances. 
It is populated from the `tasks.json` file produced by the data generation scripts. 
'''
class Task:

    # Define a class variables that acts as a map of all known task instances. 
    ALL_TASK_INSTANCES = {}

    def __init__(self, data):
        self.id = data["id"]
        self.type = data["type"]
        self.parameterized_text = data["parameterized_text"]
        self.parameters = data["parameters"]
        self.instances = [TaskInstance(self, x) for x in data["instances"]]

        if self.type == 'Information Seeking':
            self.answer_type = data["answer_type"]
        
        if self.type == 'Side-effect':
            self.answer_type = None

        # Register task instances in TASK_INSTANCES class variable.
        for instance in self.instances:
            Task.ALL_TASK_INSTANCES[instance.id] = instance


class TaskInstance:

    def __init__(self, parent_task, data):
        self.id = data["id"]
        self.parent_task = parent_task
        self.instance_text = data["instance_text"]
        self.mapping = data["mapping"]
        
        if parent_task.type == 'Side-effect':
            '''
            If the parent task is a side-effect task, the answer key will be in the form of a JSON Array
            containing objects with 'method', 'path' and 'request_kv' fields.
            '''
            self.answer_key = [SideEffectAnswer(x) for x in data["answer_key"]]
        elif parent_task.type == "Information Seeking":
            '''
            If the parent task is an information seeking task the answer key will be a JSON object containing a single key, whose value is either a literal or
            an array of literals. The key's name will be the format of the expected answer 'Number', 'Date Time' or 'Text'. 
            '''
            self.answer_key = InformationSeekingAnswer(data["answer_key"])
        else:
            print (f"Unknown parent task type: {self.parent_task.type} cannot parse answer_key for task instance {self.id}")
        


class SideEffectAnswer:

    def __init__(self, data):
        self.method = data["method"]
        self.path = data["path"]
        self.request_kv = data["request_kv"]

class InformationSeekingAnswer:

    date_format = "%Y-%m-%d %H:%M"

    def __init__(self,data):
        self.type = list(data.keys())[0]
        
        if self.type == 'Numeric' or self.type == 'Text':
            self.answer = data[self.type]
        
        if self.type == 'Date Time':
            self.answer = datetime.strptime(data[self.type], InformationSeekingAnswer.date_format)
    
    def has_multiple_answers():
        return isinstance(self.answer, list)

    def parse_date_time_answer(self, output):
        answer_search = re.search("(?<=Answer: )[0-9]{4}-[0-9]{1,2}-[0-9]{1,2} [0-9]{1,2}:[0-9]{2}", output, re.DOTALL)
        
        if answer_search is not None:
            string_date = answer_search.group(1)
            return datetime.strptime(string_date, InformationSeekingAnswer.date_format)

        return None

    def parse_numeric_answer(self, output):
        answer_search = re.search("(?<=Answer: )[0-9]+.[0-9]+)")
        if answer_search is not None:
            return float(answer_search.group(1))
        
        answer_search = re.search("(?<=Answer: )[0-9]+")
        if answer_search is not None:
            return int(answer_search.group(1))

        return None

    def parse_text_answer(self, output):
        answer_search = re.search("(?<=Answer: ').*(?=')", output, re.DOTALL)
        
        if answer_search is not None:
            return answer_search.group(1)
        
        return None

class WebVoyagerOutput:

    def __init__(self, file, instance_id):
        self.task_instance = instance_id
        self.file = file
        self.messages = json.load(file)

        # Sanity check that the last entry in the messages log is a response from the LLM. IE: the role type of the message is 'assistant'.
        if self.messages[-1]["role"] != 'assistant':
            print(f"Invalid interact_messages.json for task instance: {self.task_instance}, last entry should specify 'assistant' as the role, but instead was '{self.messages[-1]["role"]}'")

        self.output = self.messages[-1]["content"]
        self.file.close()


class WebVoyagerNetworkLog:

    @staticmethod
    def to_network_log(path):
        for instance_id in Task.ALL_TASK_INSTANCES:
            if instance_id in path:
                return WebVoyagerNetworkLog(open(path, 'r'), instance_id)
        
        print(f"Path: {path} does not contain any task instance id.")
        return None


    def __init__(self, file, instance_id):
        self.task_instance = instance_id
        self.file = file
        self.network_events = json.load(file)
        self.file.close()

        print(f"Loaded {len(self.network_events)} network events from {self.file.name} for task {self.task_instance}")


class Evaluator:

    def __init__(self):
        self.network_events = {}
        self.outputs = {}
        self.tasks = []
        

    def status(self):
        print(f"Tasks: {len(self.tasks)}\nTask Instances: {len(Task.ALL_TASK_INSTANCES)}\nNetwork Logs: {len(self.network_events)}\nOutputs: {len(self.outputs)}")

    def register_tasks(self, tasks):
        self.tasks = tasks
        print(f"{len(self.tasks)} tasks with {len(Task.ALL_TASK_INSTANCES)} instances defined in Evaluator!")

    def register_network_events(self, instance_id, events):
        self.network_events[instance_id] = events

    def register_output(self, instance_id, output):
        self.outputs[instance_id] = output

    def validate(self):

        if len(self.network_events) != len(self.outputs):
            print(f"Mismatching numbers of network logs ({len(self.network_events)}) to outputs ({len(self.outputs)})")

    def evaluate(self):
        
        self.validate()

        number_correct = 0
        number_incorrect = 0
        detailed_report = []

        for instance_id in self.outputs:
            result = self.evaluate_instance(instance_id, self.network_events[instance_id], self.outputs[instance_id])

            if result["correct"]:
                number_correct += 1
            else:
                number_incorrect += 1

            detailed_report.append(result)

        pass
    

    def evaluate_instance(self, instance_id, network_events, output):
        print(f"Evaluating task instance {instance_id}")


        instance_reference = Task.ALL_TASK_INSTANCES[instance_id]
        parent_task = instance_reference.parent_task

        if parent_task.type == 'Side-effect':

        elif parent_task.type == 'Information Seeking':

            if parent_task.answer_type == 'Text':
                observed_answer = instance_reference.parse_text_answer(self.outputs[instance_id])

            elif parent_task.answer_type == 'Numeric':
                observed_answer = instance_reference.parse_numeric_answer(self.outputs[instance_id])
            
            elif parent_task.answer_type == 'Date Time':
                observed_answer = instance_reference.parse_date_time_answer(self.outputs[instance_id])

            else:
                print(f"Unknown answer type: {parent_task.answer_type}")

            reference_answer = instance_reference.answer_key.answer
                
            eval_result = {
                "id": instance_id,
                "observed_answer": observed_answer,
                "reference_answer": reference_answer,
                "correct": observed_answer == reference_answer
            }
            
            return eval_result

        else:
            print(f"Unknown task type: {parent_task.type}") 




