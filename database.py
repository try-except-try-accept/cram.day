import gspread
from config import DB_MODE

import sqlite3
from config import *
from flask import flash
# db plan
###############################
# user chooses topics -> db updates session table flags
# server generates question -> db selects from question table and updates session table counts
# user answers question -> db updates answers table, db returns leaderboard data
# daemon/periodic update -> server updates questions table based on gspread
from datetime import datetime
from random import sample, shuffle


def authenticate_user(username, password):

    if not (username+password).isalnum():
        flash("Illegal chars in username / password.")
        return False


    q = f'SELECT user_id, nickname FROM users WHERE username="{username}" AND code="{password}" LIMIT 1'

    result = query_db(q)

    print(result)

    if result is None or len(result) == 0:
        return None

    else:
        return {'user_id':str(result[0][0]).strip(), 'display_name':result[0][1].strip(), 'username':username}



def query_db(query):

    """Connect to and execute db query"""

    if DB_MODE == "lite":
        conn = sqlite3.connect("db/fill_the_gaps.db")
        cursor = conn.cursor()


    res = None

    print("Executing")
    print(query)

    try:

        res = cursor.execute(query)
        if res is not None:
            res = res.fetchall()

        conn.commit()
        conn.close()
        print(res)
        print("Wrote to database")

        return res
    except Exception as e:
        conn.close()
        print(e)
        input()

        return None


def test():

    args = (9234, 'bob')
    args = (9234, 'bob')

    query_db('INSERT INTO users VALUES (?, ?, "werfwe")', args)

def load_question_data_to_db():
    """Connects to google sheet and updates question data
    run periodically according to quota"""

    gc = gspread.service_account(filename="secret/cram-revision-app-5da8bea462ae.json")
    sh = gc.open('CRAM Data Source')

    fill_gaps = sh.worksheet('fill_gaps')
    data = fill_gaps.get('A2:E1000')

    q = "INSERT INTO questions (question_id, question, gaps, topic_index) VALUES "
    for row in data:
        print(row)
        if row[4]:
            q +=  f'  ({row[0]}, "{row[1]}", "{row[2]}", "{row[3]}"),\n'


    q = q[:-2] + ";"
    print(q)
    query_db(q)


def check_sanitised(topics=None, not_null_ids=None, null_ints=None):
    if topics:
        for t in topics:
            if not t.replace(".", "").isdigit():
                print("invalid topic", t)
                return False

    if not_null_ids:
        for id_ in not_null_ids:
            if not str(id_).isdigit():
                print("invalid id", id_)
                return False

    if null_ints:
        for num in null_ints:
            if not (str(num).isdigit() or num is None):
                print("invalid integer (allow null)", num)
                return False

    return True


def write_session_to_db(topics, q_repeat, user_id):
    """Update session table with user's chosen topics
    count will be null if infinite repeats allowed"""



    if not check_sanitised(topics=topics, not_null_ids=[user_id], null_ints=[q_repeat]):
        flash("Problem writing to database.", "error")
        return

    if q_repeat is None:
        q_repeat = "NULL"

    topics = ",".join([f'"{t}"' for t in topics])
    q = f'''UPDATE sessions
SET in_use_flag = CASE WHEN questions.topic_index IN ({topics}) THEN 1 ELSE 0 END, gen_count = {q_repeat}
FROM questions
WHERE sessions.user_id = {user_id} AND questions.question_id = sessions.question_id;'''

    q2 = f'''
INSERT OR IGNORE INTO sessions (user_id, question_id, in_use_flag, gen_count)
SELECT {user_id}, questions.question_id, 1, {q_repeat}
FROM questions, sessions
WHERE questions.topic_index IN ({topics})
'''

    print(q)
    query_db(q)
    print(q2)
    query_db(q2)

def get_misnomers(correct):
    q = '''SELECT gaps FROM questions'''

    results = query_db(q)

    keywords = []



    for row in results:
        keywords += [word for word in row[0].split(", ")]


    print(keywords)

    misnomers = sample(keywords, 10)
    for c in correct:
        while c in results:
            misnomers = sample(keywords, 10)


    misnomers += correct

    shuffle(misnomers)

    return misnomers




def get_question_data(user_id):
    """Generates a question and updates session table"""
    q = '''SELECT questions.question_id, questions.question, questions.gaps, sessions.gen_count
    FROM questions, sessions
    WHERE questions.question_id = sessions.question_id
    AND sessions.user_id = 0
    AND sessions.in_use_flag = 1
    ORDER BY Random()
    LIMIT 1;'''

    question_id, question_text, gaps, count = query_db(q)[0]

    if count is not None:
        count -= 1
        q = f'''
UPDATE sessions
SET gen_count = {count}
WHERE question_id = {question_id} AND user_id = {user_id}
'''
        query_db(q)

    return question_text, gaps



def save_answers_to_db(user_id, answers, scores):
    """Writes the most recent answer to the database"""

    q = '''
INSERT INTO answers (answer, correct, user_id, time_stamp) VALUES '''


    q += ",".join(f'("{answer}", {score}, "{user_id}", {int(datetime.now().timestamp())})' for answer, score in zip(answers, scores))

    query_db(q)


def read_leaderboard_from_db():
    """Returns overall leaderboard and last hour leaderboard"""

    q = '''
    SELECT
       answers.user_id as user,   
       users.username,
       users.nickname,
       SUM(answers.correct) as overall
    FROM
       answers, users
    WHERE
        answers.user_id = users.user_id
    GROUP BY
        users.user_id
    HAVING
        user = answers.user_id
    ORDER BY overall DESC
    LIMIT 10'''

    overall_leaderboard = query_db(q)

    q2 = f'''
SELECT
   answers.user_id as user,
   users.username,   
   users.nickname,
   SUM(answers.correct) as overall
FROM
   answers, users
WHERE
	answers.user_id = users.user_id
	AND answers.time_stamp > {datetime.now().timestamp() - ONE_DAY} 
GROUP BY
	users.user_id
HAVING
	user = answers.user_id
ORDER BY overall DESC
LIMIT 10'''

    last_hour_leaderboard = query_db(q2)

    return overall_leaderboard, last_hour_leaderboard


if __name__ == "__main__":

    generate_question(0)