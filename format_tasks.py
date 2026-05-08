#!/usr/bin/env python3
"""
Unified task formatting script for OdoBotNL and WebVoyager formats.
Converts task definitions into the appropriate format for execution.

Usage:
    python format_tasks.py --input <path> [--format <format>] [--random-sample <n>] [--odobot-output <path>] [--webvoyager-output <path>]

Options:
    --input/-i              Path to input tasks JSON file (required)
    --format/-f             Output format: 'odobot', 'webvoyager', or 'both' (default: both)
    --random-sample/-r      Number of random instances per task (default: all)
    --odobot-output/-o      Output path for OdoBotNL JSON (default: odobot_tasks.json)
    --webvoyager-output/-w  Output path for WebVoyager JSONL (default: webvoyager_tasks.jsonl)
    --csv                   Also generate CSV output for OdoBotNL tasks (default: False)
"""

import json
import csv
import random
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


class TaskFormatter:
    """Handles formatting of tasks for different platforms."""
    
    def __init__(self, tasks_data: List[Dict[str, Any]]):
        """Initialize with task data."""
        self.tasks = tasks_data
        self._selected_instances = {}  # Cache for pre-selected instances
    
    @staticmethod
    def _build_task_text(instance: Dict[str, Any], task_type: str, 
                         answer_type: Optional[str] = None) -> str:
        """Build the final task text with prefix and optional suffix."""
        prefix = f"Use the username: {instance['instance_username']} and password: {instance['instance_password']} to login to Canvas.\n"
        
        suffix = ""
        
        # Add suffix for Information Seeking tasks based on answer type
        if task_type == "Information Seeking":
            if answer_type == 'Date Time':
                suffix = '''
Write your answer in the following format:

Answer: YYYY-MM-DD HH:mm'''
            elif answer_type == 'Numeric':
                suffix = '''
Write your answer in the following format:

Answer: [Number]'''
            elif answer_type == 'Text':
                suffix = """
Write your answer in the following format:

Answer: '[Text]'"""
        
        return f"{prefix}{instance['instance_text']}{suffix}"
    
    def _select_instances(self, task_id: str, task: Dict[str, Any], num_samples: Optional[int] = None) -> List[Dict[str, Any]]:
        """Select instances from a task, either all or a random sample.
        
        Uses pre-selected instances if available (cached from preselect_instances).
        Otherwise selects on-demand.
        """
        # Check if instances were pre-selected
        if task_id in self._selected_instances:
            return self._selected_instances[task_id]
        
        instances = task['instances']
        
        if num_samples is None:
            # Return all instances
            return instances
        
        # Validate and return random sample
        num_available = len(instances)
        if num_samples >= num_available:
            return instances
        
        return random.sample(instances, num_samples)
    
    def preselect_instances(self, num_samples: Optional[int] = None) -> None:
        """Pre-select instances for all tasks based on sampling strategy.
        
        This ensures that when both OdoBotNL and WebVoyager formats are generated,
        they use the same random samples for each task.
        """
        self._selected_instances = {}
        
        for task_index, task in enumerate(self.tasks):
            # Skip Information Seeking tasks
            if task.get("type") == "Information Seeking":
                continue
            
            task_id = task.get('id', str(task_index))
            instances = task['instances']
            
            if num_samples is None:
                # Store all instances
                self._selected_instances[task_id] = instances
            else:
                # Store random sample
                num_available = len(instances)
                if num_samples >= num_available:
                    self._selected_instances[task_id] = instances
                else:
                    self._selected_instances[task_id] = random.sample(instances, num_samples)
    
    def format_odobot_tasks(self, num_samples: Optional[int] = None) -> List[Dict[str, Any]]:
        """Format tasks for OdoBotNL execution."""
        odobot_tasks = []
        
        for task_index, task in enumerate(self.tasks):
            # Skip Information Seeking tasks for OdoBotNL
            if task.get("type") == "Information Seeking":
                continue
            
            task_id = task.get('id', str(task_index))
            selected_instances = self._select_instances(task_id, task, num_samples)
            
            for instance in selected_instances:
                task_text = self._build_task_text(instance, task.get("type"), task.get("answer_type"))
                
                odobot_task = {
                    "odoBotNL": {
                        "id": str(instance['id']),
                        "_evalId": f"{task_index + 1}|OdoBotNL|{instance['id']}",
                        "userLocation": "http://localhost:8088/login/canvas",
                        "task": task_text
                    }
                }
                
                odobot_tasks.append(odobot_task)
        
        return odobot_tasks
    
    def format_webvoyager_tasks(self, num_samples: Optional[int] = None) -> List[Dict[str, Any]]:
        """Format tasks for WebVoyager execution."""
        webvoyager_tasks = []
        
        for task_index, task in enumerate(self.tasks):
            # Skip Information Seeking tasks for WebVoyager (following original pattern)
            if task.get("type") == "Information Seeking":
                continue
            
            task_id = task.get('id', str(task_index))
            selected_instances = self._select_instances(task_id, task, num_samples)
            
            for instance in selected_instances:
                task_text = self._build_task_text(instance, task.get("type"), task.get("answer_type"))
                
                webvoyager_task = {
                    "web": "http://localhost:8088",
                    "web_name": "Canvas LMS",
                    "description": f"Instance of task {task['id']}",
                    "id": str(instance['id']),
                    "ques": task_text
                }
                
                webvoyager_tasks.append(webvoyager_task)
        
        return webvoyager_tasks


class TaskWriter:
    """Handles writing formatted tasks to output files."""
    
    @staticmethod
    def write_odobot_json(tasks: List[Dict[str, Any]], output_path: str) -> None:
        """Write OdoBotNL tasks to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(tasks, f, indent=2)
        print(f"✓ Written {len(tasks)} OdoBotNL tasks to {output_path}")
    
    @staticmethod
    def write_odobot_csv(tasks: List[Dict[str, Any]], output_path: str) -> None:
        """Write OdoBotNL tasks to CSV file."""
        rows = [["Task ID", "Eval ID", "Task"]]
        
        for task in tasks:
            odobot_info = task["odoBotNL"]
            rows.append([
                odobot_info["id"],
                odobot_info["_evalId"],
                odobot_info["task"]
            ])
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows)
        print(f"✓ Written {len(tasks)} OdoBotNL tasks to {output_path}")
    
    @staticmethod
    def write_webvoyager_jsonl(tasks: List[Dict[str, Any]], output_path: str) -> None:
        """Write WebVoyager tasks to JSONL file."""
        with open(output_path, 'w') as f:
            for task in tasks:
                f.write(json.dumps(task) + '\n')
        print(f"✓ Written {len(tasks)} WebVoyager tasks to {output_path}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Format task definitions for OdoBotNL and/or WebVoyager execution.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate all instances in both formats
    python format_tasks.py --input tasks.json
    
    # Generate 1 random instance per task in OdoBotNL format only
    python format_tasks.py --input tasks.json --format odobot --random-sample 1
    
    # Generate 5 random instances per task in WebVoyager format
    python format_tasks.py --input tasks.json --format webvoyager --random-sample 5 --webvoyager-output output.jsonl
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Path to input tasks JSON file'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['odobot', 'webvoyager', 'both'],
        default='both',
        help='Output format (default: both)'
    )
    
    parser.add_argument(
        '-r', '--random-sample',
        type=int,
        default=None,
        help='Number of random instances per task (default: all instances)'
    )
    
    parser.add_argument(
        '-o', '--odobot-output',
        default='odobot_tasks.json',
        help='Output path for OdoBotNL JSON (default: odobot_tasks.json)'
    )
    
    parser.add_argument(
        '-w', '--webvoyager-output',
        default='webvoyager_tasks.jsonl',
        help='Output path for WebVoyager JSONL (default: webvoyager_tasks.jsonl)'
    )
    
    parser.add_argument(
        '--csv',
        action='store_true',
        help='Also generate CSV output for OdoBotNL tasks'
    )
    
    return parser.parse_args()


def load_tasks(input_path: str) -> List[Dict[str, Any]]:
    """Load tasks from JSON file."""
    try:
        with open(input_path, 'r') as f:
            tasks = json.load(f)
        print(f"✓ Loaded {len(tasks)} tasks from {input_path}")
        return tasks
    except FileNotFoundError:
        print(f"✗ Error: Input file '{input_path}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"✗ Error: Invalid JSON in '{input_path}'", file=sys.stderr)
        sys.exit(1)


def validate_arguments(args):
    """Validate command line arguments."""
    if args.random_sample is not None and args.random_sample <= 0:
        print("✗ Error: --random-sample must be a positive integer", file=sys.stderr)
        sys.exit(1)


def main():
    args = parse_arguments()
    validate_arguments(args)
    
    # Load tasks
    tasks = load_tasks(args.input)
    
    # Create formatter
    formatter = TaskFormatter(tasks)
    writer = TaskWriter()
    
    print(f"\nFormatting tasks (random sample: {args.random_sample or 'all'})...")
    
    # Pre-select instances if generating both formats (ensures same samples are used)
    if args.format == 'both':
        formatter.preselect_instances(args.random_sample)
    
    # Generate OdoBotNL format if requested
    if args.format in ['odobot', 'both']:
        odobot_tasks = formatter.format_odobot_tasks(args.random_sample)
        writer.write_odobot_json(odobot_tasks, args.odobot_output)
        
        if args.csv:
            csv_output = args.odobot_output.replace('.json', '.csv')
            writer.write_odobot_csv(odobot_tasks, csv_output)
    
    # Generate WebVoyager format if requested
    if args.format in ['webvoyager', 'both']:
        webvoyager_tasks = formatter.format_webvoyager_tasks(args.random_sample)
        writer.write_webvoyager_jsonl(webvoyager_tasks, args.webvoyager_output)
    
    print("\n✓ Task formatting complete!")


if __name__ == '__main__':
    main()
