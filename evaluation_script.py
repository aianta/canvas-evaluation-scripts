import json
import argparse
import os.path
import os

from core import *

'''
Example usage with WebVoyager results:

python evaluation_script.py -t tasks.json --wv-network-logs /home/aianta/shock_and_awe/WebVoyager --wv-interact-messages /home/aianta/shock_and_awe/WebVoyager/results/20250903_16_55_12
'''


# https://stackoverflow.com/questions/11540854/file-as-command-line-argument-for-argparse-error-message-if-argument-is-not-va
def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exits!" % arg)
    else:
        return open(arg, 'r')

def is_valid_dir(parser, arg):
    if not os.path.isdir(arg):
        parser.error("The file %s is not a directory!" % arg)
    else:
        return arg

# Initalize Arg parser
parser = argparse.ArgumentParser(description="Evaluation Scripts for Canvas Web Task Benchmark.")

# Need the user to specifiy the tasks.json file
parser.add_argument('-t', '--tasks', 
                    dest="tasks_file", 
                    required=True, 
                    help="file path of the tasks.json file produced by the data generation scripts.",
                    type=lambda x: is_valid_file(parser, x))

# Support for evaluating webvoyager task executions means we need to be able to parse resulting network logs and interaction messages.
parser.add_argument("--wv-network-logs", 
                    dest="wv_network_logs",
                    help="Path to the directory containing web voyager network logs collected while executing task(s).",
                    type=lambda x: is_valid_dir(parser, x))

parser.add_argument("--wv-interact-messages",
                    dest="wv_interact_messages",
                    help="Path to the directory containing web voyager result artifacts including folders that themselves contain interaction_messages.json files collected while executing tasks.",
                    type=lambda x: is_valid_dir(parser, x))

args = parser.parse_args()

# Initalize the Evaluator that perfoms the core evaluation logic
evaluator = Evaluator()

# Need to load task definitions first, as we use them to identify relevant artifacts when loading WebVoyager data
print (f"Loading task definitions from: {args.tasks_file.name}")

task_list = json.load(args.tasks_file)
args.tasks_file.close()
task_list = [Task(x) for x in task_list]

evaluator.register_tasks(task_list)


if args.wv_network_logs:
    print (f"Looking for WebVoyager Network Logs in: {args.wv_network_logs}")
    with os.scandir(args.wv_network_logs) as _dir:
        for entry in _dir:
            if entry.name.endswith('.json'): # If it is a json file, try and parse it as a WebVoyagerNetworkLog
                network_log = WebVoyagerNetworkLog.to_network_log(entry.path)
                if network_log is not None:
                    evaluator.register_network_events(network_log.task_instance, network_log.network_events)



if args.wv_interact_messages:
    print (f"Looking for WebVoyager Interaction Messages in: {args.wv_interact_messages}")

    '''
    Structure of WebVoyager results. The 'wv_interact_messages' path should point to a directory containing directories with names that include 
    the task instance id. Each of these directories should contain an 'interact_messages.json' file.
    '''

    with os.scandir(args.wv_interact_messages) as _dir:
        for entry in _dir:
            for instance in Task.ALL_TASK_INSTANCES:
                if instance in entry.name:
                    path_to_interact_messages = entry.path + '/interact_messages.json'

                    if os.path.exists(path_to_interact_messages) and os.path.isfile(path_to_interact_messages):
                        output_obj = WebVoyagerOutput(open(path_to_interact_messages, 'r'), instance)

                        evaluator.register_output(output_obj.task_instance, output_obj.output)

evaluator.status()

results = evaluator.evaluate()

print("===============RESULTS===============")
print(json.dumps(results, indent=4))