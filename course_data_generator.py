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

    # Define some class variables to hold users and instructors which we have already created during a generation session. 
    # Use these lists later to modify generation prompts to prevent duplicates.
    MAIN_USERS = []

    INSTRUCTORS = []

    def __init__(self, seed_data):
        self.seed_course = seed_data['courses'][0]
        self.assignments = []
        self.pages = []
        self.entity_names = {}
        self.set_valid_emails([s['email'] for s in seed_data['students']])

    def course_selection_prompt(self, existing_courses):
        return (Prompter.DEFAULT_PROMPT_INSTRUCTIONS, f"Generate the name of a university level course in a random academic field. (Eg:{existing_courses}). Try to generate something thematically distinct from all the given examples. Your output should be the name of the course and nothing else.")
        
    def set_course(self, course):
        self.course = course

    def add_entity_names(self, _type, names):
        self.entity_names[_type] = names

    def get_entity_name(self, _type):
        return self.entity_names[_type].pop()

    def add_valid_assignment(self, assignment):
        self.assignments.append(assignment)

    def add_valid_page(self, page):
        self.pages.append(page)

    def set_valid_emails(self, emails):
        self.emails = emails

    def insert_emails_into_prompt(self, prompt):
        if self.emails is None:
            raise RuntimeError("Cannot insert valid emails into prompt because self.emails == None!")
        return prompt.replace("$emails$", str(self.emails))

    def modules_prompt_template(self):

        return """
Generate new realistic values based on the following snippet in the context of a '{course}' course. The only valid values for [[Page]] are {pages}. The only valid values for [[Assignment]] are {assignments}.
```yaml
  modules:
    - name: Module 1
      workflow_state: active
      content: 
        - title: [[Page]]
          completion_requirements: "must_mark_done"
        - title: [[Assignment]]
    - name: Module 2
      workflow_state: active
      content:
        - title: [[Assignment]]
        - title: [[Assignment]]
    - name: Module 3
      workflow_state: active
      content: 
        - title: [[Page]]
          completion_requirements: "must_mark_done"
        - title: [[Assignment]]
        ```

        Your output should match the yaml format of the snippet but should replace all [[Page]] and [[Assignment]] markers with valid values, change the names of the modules to reflect the '{course}' course. 
        """.format(course=self.course, pages=str(self.pages), assignments=str(self.assignments) )

    '''
    Note: sample should be stringified YAML of data.
    '''
    def simple_prompt_template(self, sample, data, course):
        # for debugging uncomment line below
        # print(f"'@ualberta.ca' in sample: {'@ualberta.ca' in sample} | 'students' not in data: {'students' not in data} | 'instructor' not in data: {'instructor' not in data} | 'main_user' not in data: {'main_user' not in data}")
        # If users are mentioned in the sample, include a stub for listing valid user emails. 
        if '@ualberta.ca' in sample and 'students' not in data and 'instructor' not in data and 'main_user' not in data: # don't include this in the student section prompt as that's where the valid users are generated.
            return """
            Generate new realistic values based on the following snippet in the context of a '{course}' course. Only the following are valid user (student) emails: $emails$

            ```yaml
            {sample}
            ```
            
            Your output should match the yaml format of the snippet but contain different values. If the sample contains a list or collection, your generated collection should contain the same number of elements. 
            """.format(sample=sample, course=course)
        else:
            return """
            Generate new realistic values based on the following snippet in the context of a '{course}' course. 

            ```yaml
            {sample}
            ```
            
            Your output should match the yaml format of the snippet but contain different values. If the sample contains a list or collection, your generated collection should contain the same number of elements. 
            """.format(sample=sample, course=course)

    def simple_name_generation_template(self, entity_type, sample_names, course):
        seed_names_yaml = yaml.dump(sample_names, default_flow_style=False)

        return """
        Here is an example of {number_of_names} names for {entity_type} in {seed_course_name}.
        
        ```yaml
        {sample_names}
        ```

        Generate {number_of_names} distinct names for {entity_type} in the {course} course. Your output should match the yaml format of the snippet but contain different values. 
        """.format(number_of_names=len(sample_names), entity_type=entity_type, seed_course_name=self.seed_course['name'], sample_names=seed_names_yaml, course=course)

    def generate_prompts(self):

        prompts = []

        for key in self.seed_course:
            
            # Assignment, quizzes, announcements and discussions can have relatively complex objects. To minimize generation errors, generate these one object at a time rather than trying to generate the whole section at once.
            # if key in [] and isinstance(self.seed_course[key], list):
            if key in ['assignments', 'quizzes', 'announcements', 'discussions', 'groups', 'pages'] and isinstance(self.seed_course[key], list):


                singular_map = {
                    'assignments': 'assignment',
                    'quizzes': 'quiz',
                    'announcements': 'announcement',
                    'discussions': 'discussion',
                    'groups': 'group',
                    'pages': 'page'
                }

                # Create a prompt to generate unique entity names for these sections
                seed_names = [ x['title'] if key != 'groups' else x['name'] for x in self.seed_course[key]]
                

                prompt = (Prompter.DEFAULT_PROMPT_INSTRUCTIONS, self.simple_name_generation_template(key, seed_names, self.course), seed_names, key+"_names")
                prompts.append(prompt)


           
                for index, element in enumerate(self.seed_course[key]):

                    sample = element
                    yaml_string = yaml.dump(sample, default_flow_style=False)

                    prompt_inner_text = self.simple_prompt_template(yaml_string, sample, self.course) 

                    if key == 'assignments':
                        prompt_inner_text = prompt_inner_text + f"\nThe output should describe a(n) {singular_map[key]} called $entity_name$ with the same submission type as that of the example assignment above."
                    elif key == 'quizzes':
                        prompt_inner_text = prompt_inner_text + f"\nThe output should describe a(n) {singular_map[key]} called $entity_name$. Do not change the number of questions, answers or their types. Make sure all question_types match with those in the example quiz above."
                    else:
                        prompt_inner_text = prompt_inner_text + f"\nThe output should describe a(n) {singular_map[key]} called $entity_name$."

                    prompt = (Prompter.DEFAULT_PROMPT_INSTRUCTIONS, prompt_inner_text , sample, key, index) 
                    prompts.append(prompt)
            else:
                sample = {
                    f"{key}": self.seed_course[key]
                }

                yaml_string = yaml.dump(sample, default_flow_style=False) 

                '''
                Prompts should contain system/instruction prompt, the input prompt, and the sample used in the template.
                '''
                prompt = (Prompter.DEFAULT_PROMPT_INSTRUCTIONS, self.simple_prompt_template(yaml_string, sample, self.course), sample)

                if key == "main_user" and len(Prompter.MAIN_USERS) > 0:
                    # Prevent duplicate main_users
                    prompt = (prompt[0], prompt[1] + f"\n Do not use the following names and email addresses: {[(x['name'], x['email']) for x in Prompter.MAIN_USERS]}", prompt[2])

                if key == "instructor" and len(Prompter.INSTRUCTORS) > 0:
                    # Prevent duplicate instructors
                    prompt = (prompt[0], prompt[1] + f"\n Do not use the following names and email addresses: {[(x['name'], x['email']) for x in Prompter.INSTRUCTORS]}", prompt[2])

                prompts.append(prompt)
        
        # Reorder the prompts so that the modules prompt is computed last, as it depends on generated pages and assignments. 
        # https://stackoverflow.com/questions/20320702/how-do-i-move-an-element-in-my-list-to-the-end-in-python
        prompts.sort(key=lambda s: 'modules' in s[2])
        
        return prompts

    


class Validator:

    def __init__(self, seed_data):
        self.seed_data = seed_data
    
    def validate(self, artifacts):
        '''
        artifacts should be a tuple: (generated_yaml, reference_yaml)
        '''

        generated_yaml = artifacts[0]
        reference_yaml = artifacts[1]

        #print(f"Validating ---------\nReference:\n{yaml.dump(reference_yaml, default_flow_style=False, indent=4)}\nGenerated:\n{yaml.dump(generated_yaml, default_flow_style=False, indent=4)}")

        return self.does_structure_match(reference_yaml, generated_yaml)
    
    def does_structure_match(self, reference, sample, errors=None):
        if errors == None:
            errors = []

        if isinstance(reference, dict):

            for reference_key in reference:

                # If the reference value for this key is 'main user' force it to be 'main user' in the generated output as well. This should ensure the correct relationships between content and users.
                if reference[reference_key] == 'main_user':
                    sample[reference_key] = 'main_user'
                
                # If the reference value for this key is 'instructor' force it to be 'instructor' in the generated output as well. This should ensure the correct relationships between content and users.
                if reference[reference_key] == 'instructor':
                    sample[reference_key] = 'instructor'

                # Force the correct value for is_public
                if reference_key == 'is_public':
                    sample[reference_key] = True

                # Force the correct value for join_levels.
                if reference_key == 'join_level':
                    sample[reference_key] = 'parent_context_request'

                # Force correct values in generated object from reference object for these fields.              
                if reference_key in ['workflow_state', 'allowed_attempts', 'one_question_at_a_time', 'public', 'group_category', 'anonymous_peer_reviews','automatic_peer_reviews', 'intra_group_peer_reviews', 'grading_type', 'allow_rating', 'discussion_type', 'completion_requirements', 'comments_enabled', ]:
                    sample[reference_key] = reference[reference_key]

                # Catch duplicate main_users
                if reference_key == 'main_user':
                    existing_emails = [x['email'] for x in Prompter.MAIN_USERS]
                    existing_names = [x['name'] for x in Prompter.MAIN_USERS]
                    if sample[reference_key]['name'] in existing_names or sample[reference_key]['email'] in existing_emails:
                        errors.append(f"The generated main_user {sample[reference_key]} already exists!")
                        continue
                
                # Catch duplicate instructors
                if reference_key == 'instructor':
                    existing_emails = [x['email'] for x in Prompter.INSTRUCTORS]
                    existing_names = [x['name'] for x in Prompter.INSTRUCTORS]
                    if sample[reference_key]['name'] in existing_names or sample[reference_key]['email'] in existing_emails:
                        errors.append(f"The generated instructor {sample[reference_key]} already exists!")
                        continue

                # Catch errors where the LLM changes the question type
                if 'question_type' == reference_key and sample[reference_key] != reference[reference_key]:
                    errors.append(f"Question type difference between generated output and reference. Question type was {sample[reference_key]} but should have been {reference[reference_key]}.")
                    continue

                # Catch errors where the LLM changes the submission type of an assignment. 
                if 'submission_type' == reference_key and sample[reference_key] != reference[reference_key]:
                    errors.append(f"Submission type difference between generated output and reference. Submission type was {sample[reference_key]} but should have been {reference[reference_key]}.")
                    continue


                if reference_key not in sample and 'question_' not in reference_key: # quizzes will have dynamic 'question_<number>' fields. It's fine if we don't have exact matches for those.
                    errors.append(f"Failed to find {reference_key} in sample!\n{sample}")
                    continue
                
                # If the reference contains a dict at this key, ensure the structures of the value match that of the sample.
                if isinstance(reference[reference_key], dict):
                    _ , _errors = self.does_structure_match(reference[reference_key], sample[reference_key], errors)
                    errors.extend(_errors)
                    continue

                if isinstance(reference[reference_key], list):
                    _ , _errors = self.does_structure_match(reference[reference_key], sample[reference_key], errors)
                    continue
            
            return len(errors) == 0, errors
        
        if isinstance(reference, list):
            
           
            

            print(f"reference is a list with {len(reference)} items. Sample is {type(sample)}." + (f"Sample has {len(sample)} items." if isinstance(sample,list) else ""))

            if not isinstance(sample, list):
                errors.append(f"Sample value was expected to be list, but instead was {type(sample)}")

            # Ensure the main_user exists in any generated list based on a reference list where they are included.
            if 'main_user' in reference and isinstance(sample, list) and 'main_user' not in sample:
                sample.append('main_user')
            
            if len(reference) > len(sample):
                errors.append(f"reference list contains {len(reference)} elements, but sample only has {len(sample)}.")

            if len(errors) == 0:
                for index, item in enumerate(reference):
                    if isinstance(item, dict):
                        is_match, _errors = self.does_structure_match(item, sample[index], errors)
                        #errors.extend(_errors)

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

def generate_section(llm, prompter, index, prompt, generated_course, retries):
    try:

        if '$emails$' in prompt[1]:
            # Update the prompt
            if len(prompt) > 3:
                prompt = (prompt[0], prompter.insert_emails_into_prompt(prompt[1]), prompt[2], prompt[3], prompt[4])
            else:
                prompt = (prompt[0], prompter.insert_emails_into_prompt(prompt[1]), prompt[2])

        if '$entity_name$' in prompt[1]:
            # Update the prompt
            prompt = (prompt[0], prompt[1].replace("$entity_name$", f"'{prompter.get_entity_name(prompt[3])}'"), prompt[2], prompt[3], prompt[4])
        
        if 'modules' in prompt[2]:
            # Update the modules prompt
            prompt = (prompt[0], prompter.modules_prompt_template(), prompt[2])

        print(f"Prompt[{index}]: {prompt[1]}\n")
        generated_output = llm.execute_prompt(prompt)

        print(f"Output[{index}]: {generated_output}\n")

        generated_yaml = llm.extract_yaml(generated_output)

        # prompt[2] is the 3rd element of the prompt and contains the reference sample
        generation_artifacts = (generated_yaml, prompt[2])

        validation_result, errors = validator.validate(generation_artifacts)

        print(f"{len(errors)} validation errors.")


        # If the generated artifacts pass validation
        if validation_result:

            if 'main_user' in generated_yaml:
                Prompter.MAIN_USERS.append(generated_yaml['main_user'])
                print(f"MAIN_USERS: {Prompter.MAIN_USERS}")

            if 'instructor' in generated_yaml:
                Prompter.INSTRUCTORS.append(generated_yaml['instructor'])
                print(f"INSTRUCTORS: {Prompter.INSTRUCTORS}")
            
            # NOTE: as of October 2, 2025, we use a fixed set of students for all courses. Ensuring we don't duplicate student accounts. 
            # After successfully generating the students section, capture the student emails to include them in future prompts where student emails are required.
            # This should increase the probability that only valid emails are used throughout the generated data.
            # if 'students' in generated_yaml:
            #     student_emails = []
            #     for s in generated_yaml['students']:
            #         student_emails.append(s['email'])
            
            #     prompter.set_valid_emails(student_emails)


            # updated our generated course dict with the new data.

            if len(prompt) > 3: # If the prompt contains a key and index because the generated result is an item in the 'assignments', 'discussions', 'announcements', or 'quizzes' section. 
                # prompt[3] should be the key name from the reference course containing the complex objects which needed to be generated one at a time.
                if prompt[3] == 'assignments': # Still need to capture generated assignment values
                    prompter.add_valid_assignment(generated_yaml['title'])

                if prompt[3] == 'pages': # Still need to capture generated page values.
                    prompter.add_valid_page(generated_yaml['title'])

                if "_names"  in prompt[3]: # If the purpose of the prompt was just to generate some names, update the prompter with those names and move on.
                    prompter.add_entity_names(prompt[3].split('_')[0], generated_yaml)
                    return

                if prompt[3] not in generated_course:
                    generated_course[prompt[3]] = []
                
                
                generated_course[prompt[3]].append(generated_yaml) # Insert the generated item at a matching index in the generated course object.
                print(f"Inserted generated output into '{prompt[3]}' of the generated_course. Generated course currently has {len(generated_course[prompt[3]])} {prompt[3]}.")
            else:
                # Handle 'normal' section.
                generated_course.update(generated_yaml)
        else:
            if retries < 5:
                print(f"Generated data failed to pass validation:\n")
                for e_index,error in enumerate(errors):
                    print(f"[Error {e_index+1}] {error}")
                print(f"Retrying...")
                generate_section(llm, prompter, index, prompt, generated_course, retries + 1)
            else:
                print(f"Generated data failed to pass validation:\n")
                for e_index,error in enumerate(errors):
                    print(f"[Error {e_index+1}] {error}")
                print(f"Out of retries!")
        

    except yaml.scanner.ScannerError:
        if retries < 5:
            print(f"Generated yaml failed to parse, retrying.")
            generate_section(llm, prompter, index, prompt, generated_course, retries + 1)
        else:
            print(f"Generated yaml failed to parse, out of retries.")
    except yaml.parser.ParserError:
        if retries < 5:
            print(f"Generated yaml failed to parse, retrying.")
            generate_section(llm, prompter, index, prompt, generated_course, retries + 1)
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

output_structure = {
    "students": seed_data["students"],
    "courses": []
}

for i in range(args.num_courses):
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
        generate_section(llm, prompter, index, prompt, generated_course, 0)
        
    print(f"Generated course in {time.time() - start_time}s.")

    existing_courses.append(new_course)

    output_structure["courses"].append(generated_course)
    

def print_course_key(course, key):
    if key not in course:
        print(f"{key} is missing from generated course!")
    else:
        print(f"{key}: {len(course[key])}")


print(f"Generated {len(output_structure["courses"])} courses")
for course in output_structure['courses']:
    print(f"Course: {course['name']}")
    print_course_key(course, 'pages')
    print_course_key(course, 'assignments')
    print_course_key(course, 'groups')
    print_course_key(course, 'discussions')
    print_course_key(course, 'announcements')
    print_course_key(course, 'quizzes')
    print("\n")


with open(args.output_path, 'w') as file:
    yaml.dump(output_structure, file, default_flow_style=False)

print(f"Generated course(s) written to file: {args.output_path}")