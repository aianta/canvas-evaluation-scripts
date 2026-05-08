#!/usr/bin/env python3
"""
Extract task instance texts and completion status from results JSON.

Reads task instance IDs from a results JSON file and looks them up in a 
tasks YAML file to retrieve the instance text and completion status.
"""

import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def load_results(results_file: str) -> Dict:
    """Load the results JSON file."""
    with open(results_file, 'r') as f:
        return json.load(f)


def load_tasks(tasks_file: str) -> Dict[str, Tuple[str, str]]:
    """
    Load tasks from YAML file and build a lookup dictionary.
    
    Returns:
        Dict mapping instance_id -> (instance_text, task_type)
    """
    with open(tasks_file, 'r') as f:
        tasks_data = yaml.safe_load(f)
    
    instance_lookup = {}
    for task in tasks_data:
        task_type = task.get(':type', 'Unknown')
        instances = task.get(':instances', [])
        
        for instance in instances:
            instance_id = instance.get(':id')
            instance_text = instance.get(':instance_text', '')
            
            if instance_id:
                instance_lookup[instance_id] = (instance_text, task_type)
    
    return instance_lookup


def extract_and_display_results(
    results_file: str,
    tasks_file: str,
    output_file: Optional[str] = None,
    format_type: str = 'text'
) -> List[Dict]:
    """
    Extract task results and match with task instances.
    
    Args:
        results_file: Path to the results JSON file
        tasks_file: Path to the tasks YAML file
        output_file: Optional output file to write results
        format_type: Output format ('text', 'json', or 'csv')
    
    Returns:
        List of extracted task results
    """
    print(f"Loading results from {results_file}...")
    results = load_results(results_file)
    
    print(f"Loading tasks from {tasks_file}...")
    instance_lookup = load_tasks(tasks_file)
    
    print(f"Processing {len(results.get('details', []))} task instances...\n")
    
    extracted_results = []
    not_found = []
    
    for detail in results.get('details', []):
        instance_id = detail.get('id')
        correct = detail.get('correct', False)
        
        if instance_id in instance_lookup:
            instance_text, task_type = instance_lookup[instance_id]
            result = {
                'instance_id': instance_id,
                'instance_text': instance_text,
                'task_type': task_type,
                'completed': correct,
                'status': 'PASS' if correct else 'FAIL'
            }
            extracted_results.append(result)
        else:
            not_found.append(instance_id)
    
    # Display results
    if format_type == 'text':
        print("=" * 100)
        print(f"{'INSTANCE ID':<40} | {'STATUS':<6} | {'TASK TYPE':<20} | INSTANCE TEXT")
        print("=" * 100)
        
        for result in extracted_results:
            status = result['status']
            instance_text_preview = result['instance_text'][:60] + "..." if len(result['instance_text']) > 60 else result['instance_text']
            print(f"{result['instance_id']:<40} | {status:<6} | {result['task_type']:<20} | {instance_text_preview}")
        
        print("=" * 100)
    
    elif format_type == 'json':
        print(json.dumps(extracted_results, indent=2))
    
    elif format_type == 'csv':
        import csv
        if output_file:
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['instance_id', 'status', 'task_type', 'instance_text', 'completed'])
                writer.writeheader()
                writer.writerows(extracted_results)
            print(f"Results written to {output_file}")
        else:
            print("CSV format requires --output argument")
    
    # Summary statistics
    print(f"\n{'SUMMARY':-^100}")
    total = len(extracted_results)
    passed = sum(1 for r in extracted_results if r['completed'])
    failed = total - passed
    
    print(f"Total instances: {total}")
    print(f"Passed:          {passed} ({100*passed/total:.1f}%)")
    print(f"Failed:          {failed} ({100*failed/total:.1f}%)")
    
    if not_found:
        print(f"\nWarning: {len(not_found)} instance IDs not found in tasks file:")
        for instance_id in not_found[:5]:  # Show first 5
            print(f"  - {instance_id}")
        if len(not_found) > 5:
            print(f"  ... and {len(not_found) - 5} more")
    
    # Write to output file if specified
    if output_file and format_type != 'csv':
        with open(output_file, 'w') as f:
            for result in extracted_results:
                f.write(f"ID: {result['instance_id']}\n")
                f.write(f"Status: {result['status']}\n")
                f.write(f"Task Type: {result['task_type']}\n")
                f.write(f"Text: {result['instance_text']}\n")
                f.write("-" * 100 + "\n\n")
        print(f"\nDetailed results written to {output_file}")
    
    return extracted_results


def main():
    parser = argparse.ArgumentParser(
        description='Extract task instance texts and completion status from results JSON'
    )
    parser.add_argument('results_file', help='Path to results JSON file')
    parser.add_argument('tasks_file', help='Path to tasks YAML file')
    parser.add_argument(
        '-o', '--output',
        help='Output file (optional, for text or csv format)',
        default=None
    )
    parser.add_argument(
        '-f', '--format',
        choices=['text', 'json', 'csv'],
        default='text',
        help='Output format (default: text)'
    )
    
    args = parser.parse_args()
    
    # Verify files exist
    if not Path(args.results_file).exists():
        print(f"Error: Results file not found: {args.results_file}")
        exit(1)
    
    if not Path(args.tasks_file).exists():
        print(f"Error: Tasks file not found: {args.tasks_file}")
        exit(1)
    
    extract_and_display_results(
        args.results_file,
        args.tasks_file,
        args.output,
        args.format
    )


if __name__ == '__main__':
    main()
