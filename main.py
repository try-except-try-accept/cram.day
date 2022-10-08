from flask import Flask, session, url_for, render_template, request, Markup, jsonify, redirect, flash

import json
import gspread


from random import choice, randrange, shuffle, sample, randint
from uuid import uuid4

from database import write_session_to_db, get_question_data,save_answers_to_db, read_leaderboard_from_db, \
                     get_misnomers, authenticate_user, load_user_creds, sync_data_with_db, save_settings_to_db, \
                     get_settings_from_db, get_topic_data


from waitress import serve
from user import User

from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from helpers import get_chart


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

        kw = gaps.replace("\,", "/////")
        kw = kw.split(", ")
        kw = [w.replace("/////", ",") for w in kw]

        for i in range(session['difficulty']):
            try:
                replacements.append(kw.pop(randrange(0, len(kw))))
            except:
                pass

        session['correct'] = []
        html_out = ""


        i = 0
        question_tokens = question.split(" ")

        skip = 0

        for y, word in enumerate(question_tokens):
            if skip:
                skip -= 1
                continue

            replacement_added = False
            for rep_word in replacements:

                if rep_word in word:
                    session['correct'].append(rep_word)
                    add_field = " " + word.replace(rep_word, f'''<input autocomplete="off" class="gap_textfield"
                                                                type="text" 
                                                                ondrop="drop(event)" ondragover="allow_drop(event)"
                                                                id="answer{i}"
                                                                name="answer{i}" required'
                                                             f'>''') + " "
                    html_out += add_field
                    replacement_added = True
                    i += 1
                elif " " in rep_word:
                    parts = rep_word.split(" ")
                    multi_part_gap_found = True

                    for x in range(len(parts)):
                        next_token_index = y+x

                        if next_token_index >= len(question_tokens) or parts[x] != question_tokens[next_token_index]:
                            multi_part_gap_found = False
                            break
                    if multi_part_gap_found:

                        session['correct'].append(rep_word)
                        skip = x

                        add_field = " " + f'<input autocomplete="off" class="gap_textfield" type="text" name="answer{i}" required>'
                        html_out += add_field
                        replacement_added = True



            if not replacement_added:
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

        print("Received answers", answers)
        print("Corrected answers", replacements)

        for correct_answer in replacements:

            if len(answers) and correct_answer.lower() == answers.pop(0).lower():
                feedback.append(None)
                result = 1


            else:
                feedback.append(correct_answer)
                result = 0

            score.append(result)
            session['win_streak'].append(result)
            if len(session['win_streak']) == 11:
                session['win_streak'].pop(0)
            session['lose_streak'].append(result)
            if len(session['lose_streak']) == 6:
                session['lose_streak'].pop(0)

        print("The score was", score)

        save_answers_to_db(current_user.user_id, answers_copy, score)
        session['scores'].append(round(sum(score)/len(score)))



        message = ""



        win_streak = session['win_streak']
        lose_streak = session['lose_streak']

        print("win streak is", win_streak)
        print("lose streak is", lose_streak)

        if len(lose_streak) == 5 and sum(lose_streak) == 0:
            message = "5 incorrect in a row! :("
            if session['difficulty'] > 1:
                session['difficulty'] -= 1
            session['lose_streak'] = []

        if len(win_streak) == 10 and sum(win_streak) == 10:
            message = "10 correct in a row! :)"
            session['difficulty'] += 1
            session['win_streak'] = []


        overall = str(round(sum(session['scores']) / len(session['scores']), 2) * 100) + "%"
        response = {'feedback':feedback,
                    'scores':score,
                    'total':overall,
                    'message':message,
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

    q = create_question()
    if q == 404:
        flash("No questions found.")
        return ""
    else:
        return q


#############################################################################

@app.route("/fill_the_gaps", methods=["GET"])
def fill_the_gaps():
    if current_user.is_authenticated:


        chart = get_chart()

        if session.get('scores') is None:
            session['scores'] = []
            session['difficulty'] = 1
            session['win_streak'] = []
            session['lose_streak'] = []

        eal = session['eal']

        print("eal mode is", eal)
        print("Topic data is", session['topic_data'])
        return render_template("fill_the_gaps.html", chart=chart, eal=eal, hide_non_topic=session['hide_non_topic'], opt_out=session['opt_out'], topic_data=session['topic_data'])

    else:
        return redirect(url_for('login'))

#############################################################################

@app.route("/get_hints", methods=["GET"])
def get_hints():
    if current_user.is_authenticated:

        eal_mode = session['eal']

        num_hints = 5 if eal_mode else 10


        hints = session['correct']

        hints = get_misnomers(hints, current_user.user_id, num_hints)

        shuffle(hints)

        final_hints = []

        for h in hints:
            this_hint = {}
            this_hint['text'] = h
            this_hint['colour'] = "#" + "".join([hex(randrange(200, 255))[2:].zfill(2) for i in range(3)])

            final_hints.append(this_hint)
            print(final_hints)


        return jsonify({"hints":final_hints, "eal_mode":eal_mode})

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
    else:
        return redirect(url_for("fill_the_gaps"))

@app.route("/save_settings", methods=["POST"])
def save_settings():
    if current_user.is_authenticated:
        eal = request.form.get("eal_mode_toggle")
        no_non_topic = request.form.get("hide_non_topic_toggle")
        opt_out = request.form.get("opt_out_toggle")
        print("Save settings")
        print(eal, no_non_topic, opt_out)
        save_settings_to_db(eal, no_non_topic, opt_out, current_user.user_id)
        session['eal'], session['hide_non_topic'], session['opt_out'] = [True if i == "true" else False for i in [eal, no_non_topic, opt_out]]
        return "200"
    else:
        return "404"

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



        creds = load_user_creds(username=username)

        if creds is None:
            flash('Login Unsuccessful.')
        else:
            user_id, username, nickname, code = creds

            this_user = load_user(user_id)


            if username == this_user.username and password == this_user.password:
                login_user(this_user)
                flash('Logged in successfully ' + username + " - now choose your topics!")
                session['eal'], session['hide_non_topic'], session['opt_out'] = get_settings_from_db(user_id)[0]
                session['topic_data'] = get_topic_data()
                return redirect(url_for('fill_the_gaps'))
            else:
                flash('Login Unsuccessful.')



    return render_template("login.html")


if __name__ == "__main__":

    serve(app, host='0.0.0.0', port=8080)
