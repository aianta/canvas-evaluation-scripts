import json
import re
import regex
from datetime import datetime
from urllib.parse import urlparse
from urllib.parse import parse_qs

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
        self.answer = None

        if self.type == 'Numeric' or self.type == 'Text' or self.type == 'Number':
            self.answer = data[self.type]
        
        if self.type == 'Date Time':
            self.answer = datetime.strptime(data[self.type], InformationSeekingAnswer.date_format)
    
    def has_multiple_answers():
        return isinstance(self.answer, list)

    def parse_date_time_answer(self, output):
        answer_search = re.search("(?<=Answer: )[0-9]{4}-[0-9]{1,2}-[0-9]{1,2} [0-9]{1,2}:[0-9]{2}", output, re.DOTALL)
        
        if answer_search is not None:
            string_date = answer_search.group(0)
            return datetime.strptime(string_date, InformationSeekingAnswer.date_format)

        answer_search = re.search("(?<=ANSWER; )[0-9]{4}-[0-9]{1,2}-[0-9]{1,2} [0-9]{1,2}:[0-9]{2}", output, re.DOTALL)
        if answer_search is not None:
            string_date = answer_search.group(0)
            return datetime.strptime(string_date, InformationSeekingAnswer.date_format)

        return None

    def parse_numeric_answer(self, output):
        answer_search = re.search("(?<=Answer: )[0-9]+.[0-9]+", output)
        if answer_search is not None:
            return float(answer_search.group(0))
        
        answer_search = re.search("(?<=Answer: )[0-9]+", output)
        if answer_search is not None:
            return int(answer_search.group(0))

        answer_search = re.search("(?<=ANSWER;) [0-9]+", output)
        if answer_search is not None:
            return int(answer_search.group(0))

        return None

    def parse_text_answer(self, output):
        answer_search = re.search("(?<=Answer: ').*(?=')", output, re.DOTALL)
        
        if answer_search is not None:
            return answer_search.group(0)
        
        answer_search = re.search("(?<=ANSWER; ').*(?=')", output, re.DOTALL)
        if answer_search is not None:
            return answer_search.group(0)

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

class NetworkEvent:

    @staticmethod
    def to_network_event(raw_event):

        # Expecting method@params>request>method within a raw event json object
        method = raw_event["params"]["request"]["method"]
        
        # Expecting url@params>request>url within the a raw event json object
        parse_result = urlparse(raw_event["params"]["request"]["url"])
        path = parse_result.path 
        # Our ground truth api_calls combine paths and queries into a single 'api_path' field.
        if parse_result.query: # So if there is a query component append it to the path
            path = path + '?' + parse_result.query

        if "postData" in raw_event["params"]["request"]:    

            # Expecting postData@params>request>postData within a raw event json object
            postData = raw_event["params"]["request"]["postData"]

            '''
            the request_body in a NetworkEvent should always be a dict. So we need to process whatever we have into that.
            There are two cases of interest:
            - postData contains a stringified JSON object
            - postData contains form data
            '''
            request_data = None

            # We can check the kind of request data in the headers
            # Expecting content-type@params>request>headers>content-type in a raw even json object
    
            try:        
                content_type = raw_event["params"]["request"]["headers"]["Content-Type"]
            except KeyError:
                content_type = raw_event["params"]["request"]["headers"]["content-type"]

            '''
            Extracts just the content type, ignoring other values in the header. IE: ; charset=UTF-8 
            '''
            content_type = NetworkEvent.parse_content_type_header(content_type)
            

            if content_type == 'application/json':
                request_data = json.loads(postData)
            elif content_type == 'application/x-www-form-urlencoded':
                request_data = parse_qs(postData)
            else:
                raise RuntimeError(f"Unsupported request content-type: {content_type} for postData:\n{postData}")


            result = NetworkEvent(method, path, request_data)

            return result

        else:

            return NetworkEvent(method, path, {})

    @staticmethod
    def parse_content_type_header(value):
        # print(f"prasing content-type value: {value}")
        search = re.search(".+/.+(?=;)|.+/.+", value)
        if search is not None:
            return search.group(0)

        print(f"Failed to parse content-type header value: {value}")
        return None
            

    def __init__(self, method, path, request_body):
        self.method = method
        self.path = path

        '''
        By the time we get to here, form data stuff should have been processed into a dict.
        '''
        if not isinstance(request_body, dict):
            raise RuntimeError(f"request_body must be a dict. Got {type(request_body)}")

        self.request = request_body

    def get_path_without_query(self):
        try:
            return self.path[0: self.path.index('?')]
        except ValueError:
            return self.path


    '''
    Returns true if:
     - the network event matches the provided path & method
     - the network event's request contains the the key-value pairs described in request_kv
    
    Additionally returns a list of errors, IE: if it returns false, the reasons for returning false will be provided in the error list.
    '''
    def matches(self, method, path, request_kv):

        errors = []

        if self.method != method:
            errors.append(f"The expected method was {method} but the observed method was: {self.method}")
        

        if "[[ANY]]" in path: # Handle [[ANY]] wild card in path reference
            path_regex = path.replace("[[ANY]]", ".+")
            print(f"reference path contains '[[ANY]]', rewrote path to the following regex: {path_regex}")

            path_search = re.search(path_regex, self.path)
            if path_search is None:
                errors.append(f"The observed path: {self.path} did not match the expected path regex: {path_regex}")
        

        elif self.path != path:
            # If the reference path does not contain a query component (?key=value), then try matching the observed path without a query component to the reference path and see if that works.
            if not '?' in path and self.get_path_without_query() == path:
                pass
            else:
                errors.append(f"The expected path was {path} but the observed path was: {self.path}")
            

        # Don't bother checking request values if method and path have already mismatched.
        if len(errors) > 0:
            return len(errors) == 0, errors

        missing_kv = False
        # If method and path look ok, dive into the request kvs
        for key, value in request_kv.items():
            # key and value here are the reference keys and values
            if key.startswith("_"): # Skip meta keys
                continue

            if not self.request_contains(key, value, self.request):
                errors.append(f"Could not find kv pair in request satisfying: '{key}':'{value}'")
                missing_kv = True

        # If missing kv flag has been tripped add a copy of the request to the errors log.
        if missing_kv:
            errors.append(json.dumps(self.request, default=str))

        return len(errors) == 0, errors # Return true if there were no matching errors
        

    '''
    Recursively explores the request looking for specific key value pair.
    Returns True if the provided key and corresponding value was found inside the request.
    '''
    def request_contains(self, key, value, request):
        print(f"Looking for {key}: {value} in request")
        for request_key, request_value in request.items():

            # If the value is itself a dict, dive into it and look for the specified kv there.
            if isinstance(request_value, dict):
                return self.request_contains(key, value, request_value)

            # Handle dynamic value cases.
            # If the key and value match return True
            if key == request_key and value == request_value:
                return True
            
            # If the reference value isn't a string and doesn't match the request value, then this is a mismatch.
            elif not isinstance(value, str) and value != request_value:
                return False

            elif key == request_key and value == "[[ANY]]":
                return True

            elif key == request_key and value.startswith("[[_array_contains="):
                if not isinstance(request_value, list):
                    raise RuntimeError(f"Expected '{key}' value to be an array because reference was: {value}. Instead, '{key}' value was of type: {type(request_value)}")
                
                target_element = self.extract_dynamic_value_parameter(value)

                if len(request_value) == 0:
                    # If the length of the request_value array is 0 then it doesn't contain the specified element.
                    return False
                else:
                    '''
                    Assume that arrays contain only one kind of data type.

                    And assume the only other possible data type is int.
                    '''
                    if isinstance(request_value[0], int):
                        # If the first element of the request value array is an integer, cast our target element to an int as well. 
                        target_element = int(target_element)
                    
                    # Verify that the specified element appears in the request_value array. 
                    return target_element in request_value


            elif key == request_key and value.startswith("[[_array_not_contains="):
                # Expect the request_value to be a list/array
                if not isinstance(request_value, list):
                    raise RuntimeError(f"Expected '{key}' value to be an array because reference value was: {value}. Instead, '{key}' value was of type: {type(request_value)}")

                target_element = self.extract_dynamic_value_parameter(value)

                if len(request_value) == 0:
                    # If the length of the request_value array is 0 then it doesn't contain the specified element.
                    return True
                else:
                    '''
                    Assume that arrays contain only one kind of data type.

                    And assume the only other possible data type is int.
                    '''
                    if isinstance(request_value[0], int): 
                        # If the first element of the request value array is an integer, cast our target element to an int as well. 
                        target_element = int(target_element)
                    
                    # Verify that the specified element does not appear in the request_value array. 
                    return target_element not in request_value
                    

            elif key == request_key and value.startswith("[[_starts_with="):
                if not isinstance(request_value, str):
                    raise RuntimeError(f"Expected '{key}' value to be a string because reference value was: {value}. Instead, '{key}' value was of type: {type(request_value)}")
                
                expected_start = self.extract_dynamic_value_parameter(value)

                return request_value.startswith(expected_start)

            elif key == request_key and value.startswith("[[_includes="):
                if not isinstance(request_value, str):
                    raise RuntimeError(f"Expected '{key}' value to be a string because reference value was: {value}. Instead, '{key}' value was of type: {type(request_value)}")

                included_str = self.extract_dynamic_value_parameter(value)

                return included_str in request_value
            

        
        # If nothing has matched return false.
        return False
    
    '''
    Extracts the value of a dynamic parameter from a sample.

    IE: if sample = "[[_array_not_contains='13']]" this function would return '13'.
    '''
    def extract_dynamic_value_parameter(self, sample):
        matchers = [
            r"(?<=\[\[_starts_with=').*?(?='\]\])",
            r"(?<=\[\[_includes=').*?(?='\]\])",
            r"(?<=\[\[_array_not_contains=').*?(?='\]\])",
            r"(?<=\[\[_array_contains=').*?(?='\]\])"
        ]

        for pattern in matchers:
            value_search = re.search(pattern, sample, re.DOTALL)
            if value_search is not None:
                return value_search.group(0)


        raise RuntimeError(f"Could not extract dynamic parameter value from: " + sample)



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

        # Now process the network_events into NetworkEvent objects
        self.network_events = [NetworkEvent.to_network_event(x) for x in self.network_events]

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

        return {
            "correct": number_correct,
            "incorrect": number_incorrect,
            "%_correct": round(((number_correct / (number_correct + number_incorrect))*100),2) if (number_correct + number_incorrect) > 0 else "N/A",
            "details": detailed_report
        }
    

    def evaluate_instance(self, instance_id, network_events, output):
        print(f"Evaluating task instance {instance_id}")


        instance_reference = Task.ALL_TASK_INSTANCES[instance_id]
        parent_task = instance_reference.parent_task

        if parent_task.type == 'Side-effect':
            # Side-effect tasks are evaluated by verifying that one or more reference api calls are observable in the network logs of a task. 
            # Begin by initalizing a dict whose keys are the answers we're looking for and whose values are a boolean flag which is flipped when a match is found.
            # If all values in this dict are True, the side-effect task was completed successfully.
            expected_api_invokations = {}
            for answer in instance_reference.answer_key:
                expected_api_invokations[answer] = False
            
            mismatch_report = {} # Define a dict for holding additional info about mismatches, useful for analysis/debugging
            
            for index, event in enumerate(network_events):
                
                # Go through each provided network event and see if it matches any of the ground truth side-effect answers.
                for api_call in expected_api_invokations:
                    _match, errors = event.matches(api_call.method, api_call.path, api_call.request_kv)
                    if _match:
                        expected_api_invokations[api_call] = True
                    else:
                        try:
                            if mismatch_report[index] is None:
                                mismatch_report[index] = []
                        except KeyError:
                            mismatch_report[index] = []

                        mismatch_report[index].append(errors)

            eval_result = {
                "id": instance_id,
                "correct": all(list(expected_api_invokations.values()))
            }

            # If the task is determined not to have been completed successfully, include a mismatch_report for debugging/analysis
            if not eval_result["correct"]:
                eval_result["mismatch_report"] = mismatch_report

            return eval_result

        elif parent_task.type == 'Information Seeking':
            # Information seeking tasks are evaluated by comparing a ground truth answer to the output observed from the agent.
            if not isinstance(instance_reference.answer_key, InformationSeekingAnswer):
                raise RuntimeError(f"Error: task instance answer key is not of type 'InformationSeekingAnswer' but instead is of type: {type(instance_reference.answer_key)}")

            if parent_task.answer_type == 'Text':
                observed_answer = instance_reference.answer_key.parse_text_answer(output)

            elif parent_task.answer_type == 'Numeric':
                observed_answer = instance_reference.answer_key.parse_numeric_answer(output)
            
            elif parent_task.answer_type == 'Date Time':
                observed_answer = instance_reference.answer_key.parse_date_time_answer(output)

            else:
                print(f"Unknown answer type: {parent_task.answer_type}")



            reference_answer = instance_reference.answer_key.answer

            if reference_answer is None:
                raise RuntimeError(f"reference answer cannot be None.")

            eval_result = {
                "id": instance_id,
                "observed_answer": observed_answer,
                "reference_answer": reference_answer,
                "correct": observed_answer == reference_answer if not isinstance(reference_answer, list) else observed_answer in reference_answer # Correct if reference answer matches, or if reference answer has multiple values, the observed answer is one of the allowed values.
            }

            if observed_answer is None or eval_result['correct'] == False:
                eval_result['raw_answer'] = output
            
            return eval_result

        else:
            raise RuntimeError(f"Unknown task type: {parent_task.type}")





