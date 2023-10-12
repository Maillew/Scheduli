from __future__ import print_function
from flask import Flask, request, render_template, redirect, url_for, jsonify, session
import os
import PyPDF2

import tiktoken
import secrets
import openai
from pdf_to_string import pdf_to_string, compress_outline

import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__, static_url_path='/static', static_folder='static')


enc = tiktoken.get_encoding("p50k_base")
enc = tiktoken.encoding_for_model('text-davinci-003')

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")
app.secret_key = secrets.token_hex(16)


prompt = """ Please ignore all previous instructions. Do not explain what you are doing. Do not self reference. You are an expert text analyst. You will be provided a course outline, delimited by single quotes. Your task is to extract every date for assignments, homeworks, quizzes, midterms, exams, tests, and similar, that a student will need to succeed in the course. Please list all the dates in ISO 8601 format and their corresponding task. 

For example, the sample text in single quotations “Monday Sept 11 @ Noon Delivering Your Speech  1 towards Participation Friday Sept 15 @ Noon Analyzing The Audience  1 towards Participation Friday Sept 22 @ Noon Mother Tongue + Why I am Hype About Translingualism 2 towards Participation” should return the following output “2023-09-11: Delivering Your Speech”, “2023-09-15: Analyzing the Audience” and “2023-09-22 Mother Tongue + Why I am Hype About Translingualism.” Please make 3 passes of the text, each time outputting which dates you extracted, to ensure that you do not miss a single date. Then, output all of the collective passes into one final output, with title “Final Output”. Please take your time to ensure accuracy.
"""

def generate_prompt(course_outline):
    return prompt + '"' + course_outline + '"'


@app.route('/')
def index():
    return render_template('index.html')

testDueDates = """Pass 1:
2023-09-08: Familiarity with writing proofs
2023-09-15: Homework 1
2023-09-22: Homework 2
2023-09-29: Homework 3
2023-10-06: Homework 4
2023-10-13: Homework 5
2023-10-20: Homework 6
2023-10-27: Homework 7
2023-11-03: Homework 8
2023-11-10: Homework 9
2023-11-17: Homework 10
2023-11-24: Homework 11

Pass 2:
2023-09-08: Familiarity with writing proofs
2023-09-15: Homework 1
2023-09-22: Homework 2
2023-09-29: Homework 3
2023-10-06: Homework 4
2023-10-13: Homework 5
2023-10-20: Homework 6
2023-10-27: Homework 7
2023-11-03: Homework 8
2023-11-10: Homework 9
2023-11-17: Homework 10
2023-11-24: Homework 11
2023-12-01: Final Exam

Pass 3:
2023-09-08: Familiarity with writing proofs
2023-09-15: Homework 1
2023-09-22: Homework 2
2023-09-29: Homework 3
2023-10-06: Homework 4
2023-10-13: Homework 5
2023-10-20: Homework 6
2023-10-27: Homework 7
2023-11-03: Homework 8
2023-11-10: Homework 9
2023-11-17: Homework 10
2023-11-24: Homework 11
2023-12-01: Final Exam

Final Output:
2023-09-08: Familiarity with writing proofs
2023-09-15: Homework 1
2023-09-22: Homework 2
2023-09-29: Homework 3
2023-10-06: Homework 4
2023-10-13: Homework 5
2023-10-20: Homework 6
2023-10-27: Homework 7
2023-11-03: Homework 8
2023-11-10: Homework 9
2023-11-17: Homework 10
2023-11-24: Homework 11
2023-12-01: Final Exam"""

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']

    if file.filename == '':
        return "No selected file"
    print("File Uploaded")

    if file and file.filename.endswith('.pdf'):
        course_outline = compress_outline(pdf_to_string(file))
        print(course_outline)
        print("Course Outline Generated")
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=generate_prompt(course_outline),
            temperature=0.6,
            max_tokens = 4096 - len(enc.encode(generate_prompt(course_outline)))
        )
        due_dates = response.choices[0].text
        print(due_dates)
        # due_dates = testDueDates
        lines = due_dates.strip().splitlines()
        lines.reverse()
        final_output_index = None
        final_due_dates = []
        
        for index, line in enumerate(lines):
            if "Final Output:" in line:
                final_output_index = index
                break

        if final_output_index is not None:
        # Calculate the original index from the reversed index
            for index in range(final_output_index):
                final_due_dates.append(lines[index])
        else:
            print("Phrase 'Final Output:' not found in the text")
        final_due_dates.reverse()
        final_output = []
        for info in final_due_dates: 
            try:
                date, task = info.split(': ', 1)
                print(date, task)
                final_output.append({"date": date, "name": task})
            except ValueError:
                print(f"Error parsing line: {info}")
        session['due_dates'] = final_output
        return jsonify(url=url_for('result', processed_data=final_output))
    else:
        return "Please upload a PDF file"

@app.route('/get-data')
def getData():
    return jsonify(session['due_dates'])


@app.route('/result')
def result():
    print("At Results")
    processed_data = session['due_dates'] #in the format "date: task"
    return render_template('upload.html', tasks = processed_data)


SCOPES = ['https://www.googleapis.com/auth/calendar']
@app.route('/post', methods=['POST'])
def post_data():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    #### OAuth2
    try:
        data = request.get_json()
        print(data['due_dates'])
        due = data['due_dates']
        for info in data['due_dates']: 
            date = info['date']
            task = info['name']
            print(date, task)
            addEvent(creds, date, task)
        return jsonify({'message': 'Data received and updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

def addEvent(creds, date, description):
    try:
        event = {
        'summary': description,
        'start': {
            'dateTime': date + 'T22:59:00-04:00',
        },
        'end': {
            'dateTime': date + 'T23:59:00-04:00',
        },
        }
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().insert(calendarId='primary', body=event).execute()
        print ('Event created')
    
    except HttpError as error:
        print('An error occurred: %s' % error)
        
if __name__ == '__main__':
    app.run(debug=True)
