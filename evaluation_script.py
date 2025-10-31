import json
import argparse
import os.path
import os
from zoneinfo import ZoneInfo

from core import *

'''
Example usage with WebVoyager results:

To Evaluate WebVoyager results
python evaluation_script.py -t tasks.json -o results.json --wv-network-logs /home/aianta/shock_and_awe/WebVoyager --wv-interact-messages /home/aianta/shock_and_awe/WebVoyager/results/20251014_17_54_50

To Evaluate OdoBot results
python evaluation_script.py -t tasks.json -o results.json --odobot-execution-events /home/aianta/shock_and_awe/odobot_results 

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

parser.add_argument('--answer-timezone',
                    dest="answer_timezone",
                    help="When providing date time answers to information seeking questions, what timezone will these answers be provided in? Value should be IANA time zone identifier.",
                    default="Canada/Mountain"
)

parser.add_argument('-o', '--out',
                    dest="output_path",
                    help="the path to the evaluation report this script will produce.",
                    required=True
)

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

parser.add_argument("--odobot-execution-events",
                    dest="odobot_execution_events",
                    help="Path to the folder containing Odobot execution event logs in .json format.",
                    type=lambda x: is_valid_dir(parser, x)
)

args = parser.parse_args()

# Initalize the Evaluator that perfoms the core evaluation logic
evaluator = Evaluator()

# Need to load task definitions first, as we use them to identify relevant artifacts when loading WebVoyager data
print (f"Loading task definitions from: {args.tasks_file.name}")

task_list = json.load(args.tasks_file)
args.tasks_file.close()
task_list = [Task(x) for x in task_list]

evaluator.register_tasks(task_list)

if args.odobot_execution_events:
    print (f"Looking for Odobot execution event logs in: {args.odobot_execution_events}")
    with os.scandir(args.odobot_execution_events) as _dir:
        for entry in _dir:
            if entry.name.endswith('.json'): #If it is a json file, try and parse it as a OdoBotExecutionEventLog
                event_log = OdoBotExecutionEventLog.to_execution_event_log(entry.path)
                if event_log is not None:
                    evaluator.register_network_events(network_log.task_instance, network_log.network_events)


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

evaluator.set_answer_timezone(args.answer_timezone)

evaluator.status()

results = evaluator.evaluate()

print("===============RESULTS===============")
# print(json.dumps(results, indent=4, default=str))

with open(args.output_path, 'w') as out_file:
    json.dump(results, out_file, indent=4, default=str)
