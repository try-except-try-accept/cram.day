from flask import Flask, session, url_for, render_template, request, Markup, jsonify, redirect, flash

import json
import gspread


from random import choice, randrange, shuffle, sample, randint
from uuid import uuid4

from database import write_session_to_db, get_question_data,save_answers_to_db, read_leaderboard_from_db, \
                     get_misnomers, authenticate_user, load_user_creds, sync_data_with_db

from waitress import serve
from user import User

from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user



app = Flask(__name__)
app.secret_key = uuid4().hex


login_manager = LoginManager(app)
login_manager.login_view = "login"

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
        return 404

#############################################################################

def record_answers():
    '''Write most recent 5 answers to database'''

    pass

    #############################################################################


def create_question():
    '''Choose random question based on session params'''

    if current_user.is_authenticated:
        question_data = get_question_data(current_user.user_id)

        if question_data is None:
            flash("You've answered all questions according to your current settings.", "error")
            return 404
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

        return 404

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

        save_answers_to_db(current_user.user_id, answers_copy, score)
        session['scores'].append(round(sum(score)/len(score)))
        overall = str(round(sum(session['scores']) / len(session['scores']), 2) * 100) + "%"
        response = {'feedback':feedback,
                    'scores':score,
                    'total':overall,
                    'next_question':create_question(),
                    'leaderboards':get_stats()}


        return jsonify(response)
    else:

        return 404

#############################################################################

@app.route("/begin_session", methods=["GET", "POST"])
def begin_session():
    if current_user.is_authenticated:
        out = "<p>So you want to study</p>"
        if request.method == "POST":
            topics = request.form.get("selected_topics").split(",")
            q_repeat = request.form.get("q_repeat")
            if q_repeat == "infinity":
                q_repeat = None

            print("topics is", topics)
            print("q rpeat is", q_repeat)

            write_session_to_db(topics, q_repeat, current_user.user_id)

    return create_question()


#############################################################################

@app.route("/fill_the_gaps", methods=["GET"])
def fill_the_gaps():
    if current_user.is_authenticated:

        if session.get('scores') is None:
            session['scores'] = []
            session['difficulty'] = 1


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
        return 404

#############################################################################

@login_manager.user_loader
def load_user(user_id):

    creds = load_user_creds(user_id=user_id)

    if creds is None:
        return None
    else:
        user_id, username, nick, password = creds
        return User(user_id, username, nick, password)

@app.route("/logout")
def logout():

    if current_user.is_authenticated:
        current_user = User()
        flash("You have logged out.")
    else:
        print(e)
        flash("No user to log out.", "error")

    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def home():
    return redirect(url_for(("login")))


@app.route("/db_sync")
def db_sync():
    if current_user.is_admin:
        return sync_data_with_db()

@app.route("/login", methods=["GET", "POST"])
def login():


    if current_user.is_authenticated:
        flash("You are already logged in.", "error")
        return redirect(url_for("fill_the_gaps"))

    if request.method == "POST":
        username = request.form.get("uname")
        password = request.form.get("psw")

        if not username.isalnum():
            flash("Illegal characters in username")
            return redirect(url_for("login"))



        user_id, username, nickname, code = load_user_creds(username=username)

        this_user = load_user(user_id)


        if username == this_user.username and password == this_user.password:
            login_user(this_user)
            flash('Logged in successfully ' + username)
            return redirect(url_for('fill_the_gaps'))
        else:
            flash('Login Unsuccessful.')

    return render_template("login.html")


if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=8080)
