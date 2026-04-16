#!/usr/bin/env python3
import argparse
import json
import yaml
import sys

def load_results(file_path):
    """Load results from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return {task['id']: task['correct'] for task in data['details']}
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        sys.exit(1)

def load_tasks(file_path):
    """Load tasks from a YAML file and create a mapping of task ID to instance text."""
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            task_mapping = {}
            if isinstance(data, list):
                for task in data:
                    if ':instances' in task:
                        for instance in task[':instances']:
                            if ':id' in instance and ':instance_text' in instance:
                                task_mapping[instance[':id']] = instance[':instance_text']
            return task_mapping
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        sys.exit(1)

def compare_results(first_results, second_results, first_filename, second_filename, task_mapping=None):
    """Compare results and return categorized task IDs and statistics."""
    if task_mapping is None:
        task_mapping = {}
    
    all_ids = set(first_results.keys()) | set(second_results.keys())
    
    categories = {
        'both_correct': [],
        'correct_only_one': {
            first_filename: [],
            second_filename: []
        },
        'incorrect_both': [],
        'incorrect_only_one': []
    }
    
    stats = {
        'correct_both': 0,
        'correct_only_one': 0,
        'incorrect_both': 0,
        'incorrect_only_one': 0
    }
    
    for task_id in sorted(all_ids):
        first_correct = first_results.get(task_id, None)
        second_correct = second_results.get(task_id, None)
        
        # Create task entry with ID and instance text
        task_entry = {'id': task_id}
        if task_id in task_mapping:
            task_entry['instance_text'] = task_mapping[task_id]
        
        if first_correct is True and second_correct is True:
            categories['both_correct'].append(task_entry)
            stats['correct_both'] += 1
        elif first_correct is True and second_correct is False:
            categories['correct_only_one'][first_filename].append(task_entry)
            stats['correct_only_one'] += 1
        elif first_correct is False and second_correct is True:
            categories['correct_only_one'][second_filename].append(task_entry)
            stats['correct_only_one'] += 1
        elif first_correct is False and second_correct is False:
            categories['incorrect_both'].append(task_entry)
            stats['incorrect_both'] += 1
        elif first_correct is None and second_correct is not None:
            if second_correct:
                categories['correct_only_one'][second_filename].append(task_entry)
                stats['correct_only_one'] += 1
            else:
                categories['incorrect_only_one'].append(task_entry)
                stats['incorrect_only_one'] += 1
        elif first_correct is not None and second_correct is None:
            if first_correct:
                categories['correct_only_one'][first_filename].append(task_entry)
                stats['correct_only_one'] += 1
            else:
                categories['incorrect_only_one'].append(task_entry)
                stats['incorrect_only_one'] += 1
    
    return categories, stats

def main():
    parser = argparse.ArgumentParser(description='Compare two result files.')
    parser.add_argument('first_file', help='Path to the first result file')
    parser.add_argument('second_file', help='Path to the second result file')
    parser.add_argument('--tasks', '-t', help='Path to the tasks YAML file for instance text lookup')
    parser.add_argument('--output', '-o', default='comparison.yaml', help='Output YAML file path')
    
    args = parser.parse_args()
    
    first_results = load_results(args.first_file)
    second_results = load_results(args.second_file)
    
    task_mapping = {}
    if args.tasks:
        task_mapping = load_tasks(args.tasks)
    
    categories, stats = compare_results(first_results, second_results, args.first_file, args.second_file, task_mapping)
    
    output_data = {
        **categories,
        'statistics': stats
    }
    
    with open(args.output, 'w') as f:
        yaml.dump(output_data, f, default_flow_style=False)
    
    print(f"Comparison saved to {args.output}")

if __name__ == '__main__':
    main()