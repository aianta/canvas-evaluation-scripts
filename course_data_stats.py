import yaml

with open('test_data.yaml', 'r') as seed_file:
    output_structure = yaml.safe_load(seed_file)

print("REFERENCE:")
for course in output_structure['courses']:
    print(f"Course: {course['name']}")
    print(f"Assignments: {len(course['assignments'])}")
    print(f"Pages: {len(course['pages'])}")
    print(f"Groups: {len(course['groups'])}")
    print(f"Discussions: {len(course['discussions'])}")
    print(f"Announcements: {len(course['announcements'])}")
    print(f"Quizzes: {len(course['quizzes'])}")
    print("\n")


with open("output.yaml", 'r') as f:
    output_structure = yaml.safe_load(f)

print(f"{type(output_structure)}")

print(f"Generated {len(output_structure['courses'])} courses")
for course in output_structure['courses']:
    print(f"Course: {course['name']}")
    print(f"Assignments: {len(course['assignments'])}")
    print(f"Pages: {len(course['pages'])}")
    print(f"Groups: {len(course['groups'])}")
    print(f"Discussions: {len(course['discussions'])}")
    print(f"Announcements: {len(course['announcements'])}")
    print(f"Quizzes: {len(course['quizzes'])}")
    print("\n")

print("Note that some assignments are discussion assignments which generate discussions at environment setup time, so the number of dicussions listed here may be less than the ones that will actually be inserted into Canvas.")