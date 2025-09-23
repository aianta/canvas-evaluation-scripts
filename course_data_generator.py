import yaml
import argparse
import os
import sys
import re
import time
from openai import OpenAI

class Prompter:

    DEFAULT_PROMPT_INSTRUCTIONS = """
    You are an agent responsible for producing realistic content for university courses in a yaml format. This includes social content produced by the interactions of students and instructors on a digital learning management system. Do not use the ':' character in your generated values, or remember to enclose string values in quotes if they contain ':' characters.
    """

    def __init__(self, seed_data):
        self.seed_course = seed_data['courses'][0]

    def course_selection_prompt(self, existing_courses):
        return (Prompter.DEFAULT_PROMPT_INSTRUCTIONS, f"Generate the name of a university level course in a random academic field. (Eg:{existing_courses}). Try to generate something thematically distinct from all the given examples. Your output should be the name of the course and nothing else.")
        
    def set_course(self, course):
        self.course = course

    def simple_prompt_template(self, sample, course):
        return  """
        Generate new realistic values based on the following snippet in the context of a '{course}' course. 

        ```yaml
        {sample}
        ```
        
        Your output should match the yaml format of the snippet but contain different values. If the sample contains a list or collection, your generated collection should contain the same number of elements. 
        """.format(sample=sample, course=course)

    def generate_prompts(self):

        prompts = []

        for key in self.seed_course:
            sample = {
                f"{key}": self.seed_course[key]
            }

            yaml_string = yaml.dump(sample, default_flow_style=False) 

            '''
            Prompts should contain system/instruction prompt, the input prompt, and the sample used in the template.
            '''
            prompt = (Prompter.DEFAULT_PROMPT_INSTRUCTIONS, self.simple_prompt_template(yaml_string, self.course), sample)
            prompts.append(prompt)
        
        return prompts


class Validator:

    def __init__(self, seed_data):
        self.seed_data = seed_data
    
    def validate(self, artifacts):
        '''
        artifacts should be a tuple: (generated_yaml, sample_yaml)
        '''

        generated_yaml = artifacts[0]
        reference_yaml = artifacts[1]

        print(f"Validating ---------\nReference:\n{yaml.dump(reference_yaml, default_flow_style=False, indent=4)}\nGenerated:\n{yaml.dump(generated_yaml, default_flow_style=False, indent=4)}")

        return self.does_structure_match(reference_yaml, generated_yaml)
    
    def does_structure_match(self, reference, sample):
        errors = []

        if isinstance(reference, dict):

            for reference_key in reference:

                # If the reference value for this key is 'main user' force it to be 'main user' in the generated output as well. This should ensure the correct relationships between content and users.
                if reference[reference_key] == 'main_user':
                    sample[reference_key] = 'main_user'
                
                # If the reference value for this key is 'instructor' force it to be 'instructor' in the generated output as well. This should ensure the correct relationships between content and users.
                if reference[reference_key] == 'instructor':
                    sample[reference_key] = 'instructor'

                if reference_key not in sample:
                    errors.append(f"Failed to find {reference_key} in sample!\n{sample}")
                    continue
                
                # If the reference contains a dict at this key, ensure the structures of the value match that of the sample.
                if isinstance(reference[reference_key], dict):
                    _ , _errors = self.does_structure_match(reference[reference_key], sample[reference_key])
                    errors.extend(_errors)
                    continue

                if isinstance(reference[reference_key], list):
                    _ , _errors = self.does_structure_match(reference[reference_key], sample[reference_key])
                    continue
            
            return len(errors) == 0, errors
        
        if isinstance(reference, list):

            if not isinstance(sample, list):
                errors.append(f"Sample value was expected to be list, but instead was {type(sample)}")
            
            if len(reference) > len(sample):
                errors.append(f"reference list contains {len(reference)} elements, but sample only has {len(sample)}.")

            if len(errors) == 0:
                for index, item in enumerate(reference):
                    if isinstance(item, dict):
                        is_match, _errors = self.does_structure_match(item, sample[index])
                        errors.extend(_errors)

            return len(errors) == 0, errors
        



        


class LLM:

    def __init__(self, api_key, model):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def execute_prompt(self, prompt):
        response = self.client.responses.create(
            model=self.model,
            instructions=prompt[0] if isinstance(prompt, tuple) else "",
            input=prompt[1] if isinstance(prompt, tuple) else prompt
        )

        return response.output_text
    
    # Extracts the yaml data from text output and returns a parsed yaml entity.
    def extract_yaml(self, output):
        # Handle the case where the yaml is enclosed in a markdown code block.
        if '```yaml' in output:
            yaml_search = re.search("(?<=```yaml).*(?=```)", output, re.DOTALL)
            if yaml_search is not None:
                yaml_txt = yaml_search.group(0)
                return yaml.safe_load(yaml_txt)
        else:
            # Otherwise assume we've been given yaml.
            return yaml.safe_load(output)




# https://stackoverflow.com/questions/11540854/file-as-command-line-argument-for-argparse-error-message-if-argument-is-not-va
def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exits!" % arg)
    else:
        return open(arg, 'r')

def generate_section(llm, index, prompt, generated_course, retries):
    try:
        print(f"Prompt[{index}]: {prompt[1]}\n")
        generated_output = llm.execute_prompt(prompt)

        print(f"Output[{index}]: {generated_output}\n")

        generated_yaml = llm.extract_yaml(generated_output)

        generation_artifacts = (generated_yaml, prompt[2])

        validation_result, errors = validator.validate(generation_artifacts)

        # If the generated artifacts pass validation
        if validation_result:
            # updated our generated course dict with the new data.
            generated_course.update(generated_yaml)
        else:
            if retries < 5:
                print(f"Generated data failed to pass validation:\n{errors}")
                print(f"Retrying...")
                generate_section(llm, index, prompt, generated_course, retries + 1)
            else:
                print(f"Generated data failed to pass validation:\n{errors}")
                print(f"Out of retries!")
        

    except yaml.scanner.ScannerError:
        if retries < 5:
            print(f"Generated yaml failed to parse, retrying.")
            generate_section(llm, index, prompt, generated_course, retries + 1)
        else:
            print(f"Generated yaml failed to parse, out of retries.")


# Initalize Arg Parser
parser = argparse.ArgumentParser(description="Course data generation script. This script generates sample course and user content data in a format suitable for the data generation ruby scripts responsible for configuring a canvas environment. It requires one seed course worth of test data to start.")

parser.add_argument('-i', '--input',
                    dest="seed_file",
                    help="The path to the .yaml file containing seed data to use.",
                    required=True,
                    type=lambda x: is_valid_file(parser, x))

parser.add_argument('-n', '--number-of-courses',
                    dest="num_courses",
                    help="The number of courses worth of data to generate. Each course will support the full task set.",
                    default=1,
                    type=int

)

parser.add_argument('-o', '--output',
                    dest="output_path",
                    help="The path where the generated output should be stored.",
                    default="output.yaml",
                    type=str
)

parser.add_argument('-k', '--open-ai-key',
                    dest="openai_key",
                    help="The openai API key."
)

parser.add_argument('-m', '--model',
                    dest="model",
                    help="The OpenAI model that should be used to generate the data.",
                    default="gpt-5-mini"
)

args = parser.parse_args()

# Resolve OpenAI API key from environment variables if not provided in commandline. 
if args.openai_key is None:
    args.openai_key = os.environ.get('OPENAI_API_KEY')

# If the OpenAI API key is still undefined raise a runtime error
if args.openai_key is None:
    raise RuntimeError("No OpenAI API key specified, please provide it via commandline with the '--open-ai-key' or '-k' flag or set it via an environment variable 'OPENAI_API_KEY' and try again.")

# Initalize API client.
llm = LLM(args.openai_key, args.model)

# Load seed data
seed_data = yaml.safe_load(args.seed_file)

existing_courses = [seed_data["courses"][0]["name"]]

# Initalize the prompter
prompter = Prompter(seed_data)

# Initalize the validator
validator = Validator(seed_data)

# Generate the name of the new course
new_course = llm.execute_prompt(prompter.course_selection_prompt(existing_courses))
print(f"Generating test data for {new_course}")
prompter.set_course(new_course)

# Initalize object to hold generated course content.
generated_course = {}

prompts = prompter.generate_prompts()

print(f"Need to generate {len(prompts)} elements.")

start_time = time.time()

for index, prompt in enumerate(prompts):
    generate_section(llm, index, prompt, generated_course, 0)
       
 

print(f"Generated course in {time.time() - start_time}s.")

with open(args.output_path, 'w') as file:
    yaml.dump(generated_course, file, default_flow_style=False)

print(f"Generated course written to file: {args.out_file}")