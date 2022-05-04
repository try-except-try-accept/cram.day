from flask import Flask, session, url_for, render_template, request, Markup, jsonify, redirect, flash

import json
import gspread
from random import choice, randrange, shuffle, sample, randint
from uuid import uuid4

from database import write_session_to_db, get_question_data,save_answers_to_db, read_leaderboard_from_db, \
                     get_misnomers, authenticate_user

from waitress import serve
from user import User
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)

app = Flask(__name__)
app.secret_key = uuid4().hex


current_user = User()

#############################################################################

def get_stats():
    '''Read database and return leaderboard'''

    if current_user.is_authenticated:

        overall, last_hour = read_leaderboard_from_db()

        leaderboard_data = {"overall":{}, "last_hour": {}}

        for position, row in enumerate(overall):
            username = row[1]
            points = row[3]
            leaderboard_data['overall'][username] = [position, points]

        for position, row in enumerate(last_hour):
            username = row[1]
            points = row[3]
            leaderboard_data['last_hour'][username] = [position, points]

        return leaderboard_data

    else:
        return "You must login to view the leaderboard."

#############################################################################

def record_answers():
    '''Write most recent 5 answers to database'''

    pass

    #############################################################################


def create_question():
    '''Choose random question based on session params'''

    if current_user.is_authenticated:
        question_data = get_question_data(session['user_id'])

        if question_data is None:
            flash("You've answered all questions according to your current settings.", "error")
            return redirect(url_for("fill_the_gaps"))
        question, gaps = question_data

        replacements = []
        kw = gaps.replace(" ", ",").replace(",,", ",").split(",")

        for i in range(session['difficulty']):
            replacements.append(kw.pop(randrange(0, len(kw))))

        session['correct'] = []
        html_out = ""
        print("replacements is", replacements)

        i = 0
        question_tokens = question.split(" ")

        for y, word in enumerate(question_tokens):
            for rep_word in replacements:

                if rep_word in word:
                    session['correct'].append(rep_word)
                    add_field = " " + word.replace(rep_word, f'<input class="gap_textfield" type="text" name="answer{i}" required'
                                                             f'>') + " "
                    html_out += add_field
                    i += 1
                else:
                    html_out += " " + word


        session['question'] = question

        return Markup(html_out)

    else:

        return "You must login to create a question"

#############################################################################

@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    '''Check answer and return feedback'''

    if current_user.is_authenticated:
        answers = request.form.get("answers").split(",")
        answers_copy = list(answers)
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

        save_answers_to_db(session['user_id'], answers_copy, score)
        session['scores'].append(round(sum(score)/len(score)))
        overall = str(round(sum(session['scores']) / len(session['scores']), 2)) + "%"
        response = {'feedback':feedback,
                    'scores':score,
                    'total':overall,
                    'next_question':create_question(),
                    'leaderboards':get_stats()}


        return jsonify(response)
    else:

        return "You must login to submit an answer"

#############################################################################

@app.route("/get_question", methods=["GET", "POST"])
def get_question():
    if current_user.is_authenticated:
        out = "<p>So you want to study</p>"
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
    if current_user.is_authenticated:

        if session.get('scores') is None:
            session['scores'] = []
            session['difficulty'] = 1
            session['user_id'] = 999

        return render_template("fill_the_gaps.html")

    else:
        return redirect(url_for('login'))

#############################################################################

@app.route("/get_hints", methods=["GET"])
def get_hints():
    if current_user.is_authenticated:


        hints = session['correct']

        hints = get_misnomers(hints)

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

    else:
        return "Only a logged in user can get hints"

#############################################################################

@app.route("/logout")
def logout():

    try:
        logout_user()
        flash("You have logged out.")
    except Exception as e:
        print(e)
        flash("No user to log out.", "error")

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():


    if current_user.is_authenticated:
        flash("You are already logged in.", "error")
        return redirect(url_for("question"))

    if request.method == "POST":
        username = request.form.get("uname")
        password = request.form.get("psw")


        user = User(username, password)
        if user.is_authenticated:
            current_user = user
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('fill_the_gaps'))

        else:
            flash("Invalid username / password", "error")

    return render_template("login.html")


serve(app, host='0.0.0.0', port=8080)
