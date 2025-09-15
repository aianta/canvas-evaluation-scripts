import json

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
            self.answerkey = [SideEffectAnswer(x) for x in data["answer_key"]]
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

    def __init__(self,data):
        self.type = list(data.keys())[0]
        self.answer = data[self.type]
    
    def has_multiple_answers():
        return isinstance(self.answer, list)

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
    



