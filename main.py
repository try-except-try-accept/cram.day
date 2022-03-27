from flask import Flask, session, url_for, render_template, request, Markup, jsonify

import json
import gspread
from random import choice, randrange, shuffle, sample, randint
from uuid import uuid4

from database import write_session_to_db, generate_question


app = Flask(__name__)
app.secret_key = uuid4().hex

#############################################################################

def get_stats():
    '''Read database and return leaderboard'''

    return leaderboard

#############################################################################

def record_answers():
    '''Write most recent 5 answers to database'''

    pass

    #############################################################################


def create_question():
    '''Choose random question based on session params'''


    question = generate_question('user_id')

    if len(source_data) == 0:
        return "<p>You've answered all questions on your chosen topic.</p>"

    i = randrange(0, len(source_data))
    question = session['source_data'].pop(i)


    replacements = []
    kw = question['keywords']
    for i in range(session['difficulty']):
        replacements.append(kw.pop(randrange(0, len(kw))))

    session['correct'] = []

    question = question['question']

    html_out = ""

    for word in question.split(" "):
        for rep in replacements:
            if rep in word:
                session['correct'].append(rep)
                html_out += f' <input class="gap_textfield" type="text" name="answer{i}">'
            else:
                html_out += " " + word


    session['question'] = question

    return Markup(html_out)

#############################################################################

@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    '''Check answer and return feedback'''

    answers = request.form.get("answers").split(",")

    question = session['question']
    replacements = session['correct']

    score = []
    feedback = []
    html_out = ""
    for correct_answer in replacements:

        if len(answers) and correct_answer == answers.pop(0):
            feedback.append(None)
            score.append(1)
        else:
            feedback.append(correct_answer)
            score.append(0)


    session['scores'].append(round(sum(score)/len(score)))

    overall = str(round(sum(session['scores']) / len(session['scores']), 2)) + "%"

    response = {'feedback':feedback,
                'scores':score,
                'total':overall,
                'next_question':create_question()}


    print("returned response")
    return jsonify(response)

#############################################################################

@app.route("/get_question", methods=["GET", "POST"])
def get_question():

    out = "<p>So you wanna study</p>"

    if request.method == "POST":
        topics = request.form.get("selected_topics").split(",")
        q_repeat = request.form.get("q_repeat")
        if q_repeat == "infinity":
            q_repeat = None


        print("topics is", topics)
        print("q rpeat is", q_repeat)

        write_session_to_db(topics, q_repeat, session['user_id'])

    return create_question()

#############################################################################

@app.route("/fill_the_gaps", methods=["GET"])
def fill_the_gaps():

    if session.get('scores') is None:
        session['scores'] = []
        session['difficulty'] = 1
        session['user_id'] = 0


    return render_template("fill_the_gaps.html")

#############################################################################

@app.route("/get_hints", methods=["GET"])
def get_hints():

    hints = session['correct']



    misnomers = session['misnomers']

    for i in range(6, 10):

        misnomer = choice(misnomers)
        hints.append(misnomer)

    shuffle(hints)


    final_hints = []

    for h in hints:
        this_hint = {}
        this_hint['text'] = h + "... ?"
        this_hint['colour'] = "#" + (hex(randrange(25, 200))[2:].zfill(2) * 3)
        this_hint['x'] = randrange(0, 800)
        this_hint['y'] = randrange(400, 800)
        final_hints.append(this_hint)
        print(final_hints)


    return jsonify(final_hints)

#############################################################################




app.run()