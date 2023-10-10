from __future__ import print_function

import os
import tiktoken
import secrets
import openai
from flask import Flask, redirect, render_template, request, url_for, session
from pdf_to_string import pdf_to_string

import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


enc = tiktoken.get_encoding("p50k_base")
enc = tiktoken.encoding_for_model('text-davinci-003')

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")
app.secret_key = secrets.token_hex(16)


prompt = """ Please ignore all previous instructions. Do not explain what you are doing. Do not self reference. You are an expert text analyst. You will be provided a course outline, delimited by single quotes. Your task is to extract every date for assignments, homeworks, quizzes, midterms, exams, tests, and similar, that a student will need to succeed in the course. Please list all the dates in ISO 8601 format and their corresponding task. 

For example, the sample text in single quotations “Monday Sept 11 @ Noon Delivering Your Speech  1 towards Participation Friday Sept 15 @ Noon Analyzing The Audience  1 towards Participation Friday Sept 22 @ Noon Mother Tongue + Why I am Hype About Translingualism 2 towards Participation” should return the following output “2023-09-11: Delivering Your Speech”, “2023-09-15: Analyzing the Audience” and “2023-09-22 Mother Tongue + Why I am Hype About Translingualism.” Please make 3 passes of the text, each time outputting which dates you extracted, to ensure that you do not miss a single date. Then, output all of the collective passes into one final output, with title “Final Output”. Please take your time to ensure accuracy.
"""
#need to get course outline from pdf

pdf_file = "preliminary_Chem_1301A_2023_course_outline.pdf"  # Replace with the path to your PDF file
course_outline = pdf_to_string(pdf_file)

def generate_prompt():
    return prompt + course_outline


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



@app.route("/", methods=("GET", "POST"))
def index():
    session['due_dates'] = testDueDates

    if request.method == "POST":
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=generate_prompt(),
            temperature=0.6,
            max_tokens = 4096 - len(enc.encode(generate_prompt())) #problem is that if we dont have a max token, the response will only be one line
        )
        session['due_dates'] = response.choices[0].text
        return redirect(url_for("index", result=response.choices[0].text))

    result = request.args.get("result")
    # result = testDueDates
    return render_template("index.html", result=result)

SCOPES = ['https://www.googleapis.com/auth/calendar']

@app.route("/process_due_dates")
def process_due_dates():
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

    due_dates = session.get('due_dates', [])
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
    
    
    for info in final_due_dates: 
        date, task = info.split(': ')
        addEvent(creds, date, task)
    return "Due dates processed successfully"

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
        

if __name__ == "__main__":
    app.run()