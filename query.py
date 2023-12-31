from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, db
import json
import shutil
import os
import subprocess

# Initialize OpenAI and Firebase Admin
client = OpenAI(api_key='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')
cred = credentials.Certificate('./credentials.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://labmindprototype-default-rtdb.firebaseio.com/'
})

# get schema structure
def infer_schema(node, schema=None):
    """
    Recursively traverse the Firebase Realtime Database node to infer the schema.
    """
    if schema is None:
        schema = {}

    if isinstance(node, dict):
        for key, value in node.items():
            if key not in schema:
                schema[key] = infer_schema(value, {})
            else:
                schema[key] = infer_schema(value, schema[key])
    elif isinstance(node, list):
        if node:  # non-empty list
            # Infer schema based on the first element of the list
            return [infer_schema(node[0], {})]
    else:
        # For basic data types, just store the type
        return type(node).__name__

    return schema

def generate_realtime_db_schema():
    root_ref = db.reference('/')
    root_data = root_ref.get()
    return infer_schema(root_data)


schema = generate_realtime_db_schema()


# Function to query Firebase using a query generated by OpenAI
def query_firebase_with_ai(user_input):
    prompt = f"Generate a NoSQL query for my Firebase Realtime Database based on the user input: {user_input}. Output should only be the text code to run with NOTHING ELSE, for example: ref = db.reference(\"test/experiments\").order_by_child(\"Date\").limit_to_last(1)"
    instruction = f"You generate a NoSQL queries for Firebase Realtime Database. Only output the noSQL query, here is the schema: {schema}"
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",  # Ensure this model is available to you
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": prompt}
        ]
    )
    # Extract the assistant message
    generatedMessage = response.choices[0].message.content

    print(generatedMessage)
    exec(generatedMessage, globals())
    result = ref.get()
    pretty_result = json.dumps(result, indent=4)
    print(pretty_result)

    data_dict = json.loads(pretty_result)

    file_names = [image_info['file_name'] for image_info in data_dict.values()]
    for file_name in file_names:
        print(file_name)
    return file_names

def open_files(file_names):
    for file_name in file_names:
        # Construct the absolute path to the file
        file_path = os.path.abspath(file_name)
        
        # Check if the file exists before trying to open it
        if os.path.isfile(file_path):
            # Open the file using the default application
            if os.name == 'nt':  # for Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # for macOS, Linux, Unix, etc.
                subprocess.run(['open', file_path], check=True)
            else:
                print(f"OS not supported for opening files directly: {os.name}")
        else:
            print(f"File does not exist: {file_path}")

#

user_input = "return images with working distance mm = 9.6"
file_names = query_firebase_with_ai(user_input)
print(file_names)
open_files(file_names)
