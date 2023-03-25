from flask import Flask, session, url_for, render_template, request, Markup, jsonify, redirect, flash, Response
from random import choice, randrange, shuffle, sample, randint
from uuid import uuid4
from database import write_session_to_db, get_question_data,save_answers_to_db, read_leaderboard_from_db, \
                     get_misnomers, authenticate_user, load_user_creds, sync_data_with_db, save_settings_to_db, \
                     get_settings_from_db, get_topic_data, load_gsheet, sync_answer_data



from user import User

from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from helpers import get_chart
from config import GAP_HTML, DARK_MODE_COLOURS, LIGHT_MODE_COLOURS, WAIT_BEFORE_RESYNC
from waitress import serve
import os
from time import sleep
from requests import get

app = Flask(__name__)
app.secret_key = uuid4().hex


login_manager = LoginManager(app)
login_manager.login_view = "login"


#############################################################################

def get_stats():
    '''Read database and return leaderboard'''

    if current_user.is_authenticated:
        mode = session['leaderboard_mode']

        overall, last_hour = read_leaderboard_from_db(mode)

        leaderboard_data = {"overall":{}, "last_hour": {}}

        for position, row in enumerate(overall):
            username = row[1]
            points = row[3]
            if mode == 0:   points = f"{round(points, 2)}%"
            leaderboard_data['overall'][username] = [position, points]

        for position, row in enumerate(last_hour):
            username = row[1]
            points = row[3]
            if mode == 0:   points = f"{round(points, 2)}%"
            leaderboard_data['last_hour'][username] = [position, points]

        return leaderboard_data

    else:
        return 404

#############################################################################

def record_answers():
    '''Write most recent 5 answers to database'''

    pass

#############################################################################

def reload_settings(user_id):
    session['eal'], \
    session['hide_non_topic'], \
    session['opt_out'], \
    session['leaderboard_mode'], \
    session['display_mode'], \
    session['highlight'] = get_settings_from_db(user_id)[0]

#############################################################################

def perform_replacements(question_tokens, replacements, colour_map, dark_mode):
    html_out = ""
    i, skip = 0, 0

    html_gap = GAP_HTML
    if dark_mode:
        html_gap = html_gap.replace("background-color:{colour}", "border:thin {colour} solid")


    for y, word in enumerate(question_tokens):
        if skip:
            skip -= 1
            #print("skipped", word)
            continue

        replacement_added = False
        for rep_word in replacements:

            if rep_word in word:
                #print(f"Found {rep_word} in {word}")
                session['correct'].append(rep_word)
                add_field = " " + word.replace(rep_word, html_gap.format(colour=colour_map[rep_word], i=i)) + " "
                html_out += add_field
                replacement_added = True
                i += 1
                break
            elif " " in rep_word:
                parts = rep_word.split(" ")
                multi_part_gap_found = True
                new_word = ""
                for x in range(len(parts)):
                    next_token_index = y + x

                    if next_token_index >= len(question_tokens) or parts[x] != question_tokens[next_token_index]:
                        #print("Did not find multi part gap")
                        multi_part_gap_found = False
                        break
                    else:
                        new_word += " " + question_tokens[next_token_index]
                if multi_part_gap_found:
                    #print("Found multi part gap")
                    skip = x

                    add_field = new_word

                    for part in parts:
                        #print(f"i'll replace {part} with a gap")
                        session['correct'].append(part)
                        add_field = " " + add_field.replace(part, html_gap.format(colour=colour_map[part], i=i)) + " "

                    html_out += add_field
                    replacement_added = True
                    i += 1

        if not replacement_added:
            html_out += " " + word


    return html_out

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

        dark_mode = 1 == session['display_mode']
        highlight = session['highlight']

        colours = list(DARK_MODE_COLOURS if dark_mode else LIGHT_MODE_COLOURS)
        shuffle(colours)

        static_colour = "#111111" if dark_mode else "#FEFEFE"
        #print("Highlight is", highlight)
        colour_map = {rep:colours.pop(0) if highlight else static_colour
                      for rep in " ".join(replacements).split()} # join up and resplit to handle rep words with spaces


        question_tokens = question.split(" ")




        html_out = perform_replacements(question_tokens, replacements, colour_map, dark_mode)


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
        score = []
        feedback = []
        html_out = ""

        if not all(a.strip() == "" for a in answers):

            answers_copy = list(answers)
            question = session['question']
            replacements = session['correct']


            #print("Received answers", answers)
            #print("Corrected answers", replacements)

            for correct_answer in replacements:

                if len(answers) and correct_answer.lower() == answers.pop(0).lower().strip():
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

            #print("The score was", score)

            save_answers_to_db(current_user.user_id, answers_copy, score)
            if score:
                session['scores'].append(round(sum(score)/len(score)))



            message = ""

        else:
            message = ""
            score = 0
            session['lose_streak'].append(0)
            if len(session['lose_streak']) == 6:
                session['lose_streak'].pop(0)

        win_streak = session['win_streak']
        lose_streak = session['lose_streak']

        #print("win streak is", win_streak)
        #print("lose streak is", lose_streak)

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
            everything = bool(request.form.get("everything").replace("false", ""))
            #print("was everything chosen", everything)
            if q_repeat in ["infinity", "null"]: # either default mode or everything mode
                q_repeat = None

            #print("topics is", topics)
            #print("q rpeat is", q_repeat)
            #print("everything is", everything)

            write_session_to_db(topics, q_repeat, everything, current_user.user_id)

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
        display_mode = session['display_mode']
        leaderboard_mode = session['leaderboard_mode']
        highlight = session['highlight']

        #print("eal mode is", eal)
        #print("Topic data is", session['topic_data'])
        return render_template("fill_the_gaps.html", chart=chart, eal=eal, display_mode=display_mode,
                               highlight=highlight, leaderboard_mode=leaderboard_mode,
                               hide_non_topic=session['hide_non_topic'], opt_out=session['opt_out'],
                               topic_data=session['topic_data'])

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
            #print(final_hints)


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
        user_id, username, password = creds
        return User(user_id, username, password)

@app.route("/logout")
def logout():

    if current_user.is_authenticated:
        current_user = User()
        flash("You have logged out.")
    else:
        #print(e)
        flash("No user to log out.", "error")

    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def home():
    return redirect(url_for(("login")))


@app.route("/answer_sync")
def answer_sync():    
    return sync_answer_data(load_gsheet())
    

@app.route("/all_sync")
def all_sync():

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
        highlight = request.form.get("highlight_toggle")
        leaderboard_mode = request.form.get("leaderboard_mode_dropdown")
        display_mode = request.form.get("display_mode_dropdown")
        #print("Save settings")
        #print(eal, no_non_topic, opt_out)
        save_settings_to_db(eal, no_non_topic, opt_out, leaderboard_mode, display_mode, highlight, current_user.user_id)
        session['eal'], session['hide_non_topic'], session['opt_out'], session['highlight'] = [True if i == "true" else
                                                                                               False for i in [eal,
                                                                                                               no_non_topic,
                                                                                                               opt_out,
                                                                                                               highlight]]
        reload_settings(current_user.user_id)
        session['topic_data'] = get_topic_data()
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
            user_id, username, code = creds

            this_user = load_user(user_id)


            if username == this_user.username and password == this_user.password:
                login_user(this_user)
                flash('Logged in successfully ' + username + " - now choose your topics!")
                reload_settings(user_id)
                session['topic_data'] = get_topic_data()
                return redirect(url_for('fill_the_gaps'))
            else:
                flash('Login Unsuccessful.')



    return render_template("login.html")

def create_app():
    return app


if __name__ == "__main__":

    serve(app, port="80")




