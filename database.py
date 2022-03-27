import gspread
from config import DB_MODE

import sqlite3
from flask import flash
# db plan
###############################
# user chooses topics -> db updates session table flags
# server generates question -> db selects from question table and updates session table counts
# user answers question -> db updates answers table, db returns leaderboard data
# daemon/periodic update -> server updates questions table based on gspread

def query_db(query):

    """Connect to and execute db query"""

    if DB_MODE == "lite":
        conn = sqlite3.connect("db/test_database.db")
        cursor = conn.cursor()


    res = None

    print("Executing")
    view_query = query

    try:

        res = cursor.execute(query)


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
SET in_use_flag = CASE WHEN questions.topic_index IN ({topics}) THEN 1 ELSE 0 END, count = {q_repeat}
FROM questions
WHERE sessions.user_id = {user_id} AND questions.question_id = sessions.question_id;'''
    print(q)
    query_db(q)


def generate_question(user_id):
    """Generates a question and updates session table"""




def write_answer_to_db(q_id, answer, user_id):
    """Writes the most recent answer to the database"""




def read_session_from_db():
    """Returns a question set based on user's topic settings"""



def read_leaderboard_from_db():
    """Returns overall leaderboard and last hour leaderboard"""



if __name__ == "__main__":

    test()