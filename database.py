import gspread
import sqlite3
from config import *
from flask import flash, Markup
from os import environ
# db plan
###############################
# user chooses topics -> db updates session table flags
# server generates question -> db selects from question table and updates session table counts
# user answers question -> db updates answers table, db returns leaderboard data
# daemon/periodic update -> server updates questions table based on gspread
from datetime import datetime
from random import sample, shuffle, randint, choice
from boto.s3.connection import S3Connection
from boto.exception import NoAuthHandlerFound as BotoError
from json import loads
try:
    s3 = S3Connection(environ['GOOGLE_SERVICE_ACCOUNT'])
except BotoError:
    print("Assume running locally")

def load_user_creds(user_id=None, username=None):
    if username:
        result = query_db(f'SELECT user_id, username, code from users where username = "{username}"')
    else:
        result = query_db(f'SELECT user_id, username, code from users where user_id = "{user_id}"')

    #print(result)

    if result is None or len(result) == 0:
        return None

    else:
        return result[0]


def authenticate_user(username, password):

    if not (username+password).isalnum():
        flash("Illegal chars in username / password.")
        return False


    q = f'SELECT user_id, username FROM users WHERE username="{username}" AND code="{password}" LIMIT 1'

    result = query_db(q)

    #print(result)

    if result is None or len(result) == 0:
        return None

    else:
        return {'user_id':str(result[0][0]).strip(), 'display_name':result[0][1].strip(), 'username':username}


def get_last_n_answers(n):
    return query_db("SELECT time_stamp FROM answers ORDER BY time_stamp DESC LIMIT ?", args=(n,))

def query_db(query, catch=True, args=None):

    """Connect to and execute db query"""

    if DB_MODE == "lite":
        conn = sqlite3.connect("db/fill_the_gaps.db")
        cursor = conn.cursor()


    res = None

    #print("Executing")
    #print(query)
    #if args:
        #print(args)

    try:
        if args is None:
            #print(query)
            res = cursor.execute(query)
        else:
            res = cursor.execute(query, (*args,))
        if res is not None:
            res = res.fetchall()

        conn.commit()
        conn.close()
        #print(res)
        #print("Wrote to database")

        return res
    except Exception as e:
        conn.close()
        #print(e)
        if not catch:
            input("problem")


        return None


def test():

    query_db('''INSERT OR IGNORE INTO answers VALUES (?, ?, ?, ?), (?, ?, ?, ?)''', args=("WalkHours", 1, 7, 1652146473, "WalkHours", 1, 7, 1652146474))

    input("work?")
    exit()





def spreadsheet_to_query_placeholders(data):
    """Create 1D list of query args and (?, ?) style placeholders"""
    rows = len(data)
    placeholder = "(?, ?, ?, ?), "
    all_placeholders = (placeholder * rows)

    all_data = []

    for row in data:
        all_data.extend(row)


    return all_data, all_placeholders



def sync_question_data(sh):
    
    # sync spreadsheet question data with database
    query_db("DELETE FROM questions")

    fill_gaps = sh.worksheet('fill_gaps')
    data = fill_gaps.get("A2:D2000")

    q = "INSERT INTO questions (question_id, question, gaps, topic_index) VALUES "



    # for row in data:
    #     #print(row)
    #     if row[4]:
    #         q +=  f'  ({row[0]}, "{row[1]}", "{row[2]}", "{row[3]}"),\n'

    all_data, all_placeholders = spreadsheet_to_query_placeholders(data)

    q += all_placeholders


    q = q[:-2] + ";"

    query_db(q, args=all_data)

    question_data = query_db("SELECT * FROM questions")
    question_data_conf = "<p>Data added:</p><table>" + "".join(["<tr>" + "".join([f"<td>{col}</td>" for col in row])+ \
                                                                "</tr>" for row in question_data]) + "</table>"
    
    fill_gaps = sh.worksheet('topics')
    data = fill_gaps.get("A2:C1000")
    q = "INSERT OR REPLACE INTO topics (topic_id, topic_index, topic_name, topic_category) VALUES "
    for row in data:
        index = row[1].split(" ")[0]
        name = " ".join(row[1].split(" ")[1:])
        q += f'({row[0]}, "{index}", "{name}", "{row[2]}"),'



    query_db(q[:-1])

    return question_data_conf



def sync_answer_data(sh):
    # sync database answer data with spreadsheet
    answer_data_conf = ""

    ss = sh.worksheet('answers')
    ss_answers = ss.get_all_values()

    all_data, all_placeholders = spreadsheet_to_query_placeholders(ss_answers)

    q = 'INSERT OR IGNORE INTO answers VALUES '
    q += all_placeholders


    q = q[:-2]
    query_db(q, args=all_data)

    answer_data_conf += f"Wrote (or ignored) {len(ss_answers)} answers to the db.\n"


    q = "SELECT * FROM answers"
    db_answers = query_db(q)




    answer_data_conf += "Backed up the following answers from the db:<br><ul>"

    all_answers = list(ss_answers) + list(db_answers)
    log_pks = set()
    remove_records = set()
    for index, row in enumerate(list(all_answers)):
        pk = (int(row[-1]), int(row[-2]))
        if pk not in log_pks:
            answer_data_conf += "<li>" + "\t".join(str(i) for i in row) + "</li>"
        else:
            all_answers[index] = None

        log_pks.add(pk)

    if None in all_answers:
        all_answers.remove(None)

    answer_data_conf += "</ul>"

    ss.update(f'A1', all_answers)
    return answer_data_conf

def load_gsheet():
    """Opens backup gsheet"""
    
    try:
        gc = gspread.service_account(filename=environ["GOOGLE_SERVICE_ACCOUNT"])
    except:
        gc = gspread.service_account_from_dict(loads(environ["GOOGLE_SERVICE_ACCOUNT"]))

    return gc.open('CRAM Data Source')



def sync_data_with_db():
    """Connects to google sheet and updates question data / answer data
    run periodically according to quota"""


    sh = load_gsheet()
    
    
    question_data_conf = sync_question_data(sh)
    answer_data_conf = sync_answer_data(sh)


    return Markup(question_data_conf + answer_data_conf)


def get_topic_data():

    q = '''SELECT topic_index, topic_name, topic_category FROM topics ORDER BY topic_index'''
    results = query_db(q)
    #print(results)
    topic_data = {}
    for index, topic in zip([1,2,3,4,5], ["a2", "as", "igcse", "ks3", "pp"]):
        topic_data[index] = Markup(",".join([f'"{row[0]} {row[1]}"' for row in results if row[2] == index]))

    #print(topic_data)
    return topic_data




def check_sanitised(topics=None, not_null_ids=None, null_ints=None):
    #print(topics, not_null_ids, null_ints)
    if not_null_ids:
        for id_ in not_null_ids:
            if not str(id_).isdigit():
                #print("invalid id", id_)
                return False

    if null_ints:
        for num in null_ints:
            if not (str(num).isdigit() or num is None):
                #print("invalid integer (allow null)", num)
                return False

    return True


def write_session_to_db(topics, q_repeat, everything, user_id):
    """Update session table with user's chosen topics
    count will be null if infinite repeats allowed"""



    if not check_sanitised(topics=topics, not_null_ids=[user_id], null_ints=[q_repeat]):
        flash("Problem writing to database.", "error")
        return

    if q_repeat is None:
        q_repeat = "NULL"

    topics = ",".join([f'"{t}"' for t in topics])
    q = f'''UPDATE sessions
SET in_use_flag = CASE WHEN questions.topic_index IN ({topics}) OR {everything} THEN 1 ELSE 0 END, gen_count = {q_repeat}
FROM questions
WHERE sessions.user_id = {user_id} AND questions.question_id = sessions.question_id;'''

    q = f'''UPDATE sessions
SET in_use_flag = CASE WHEN question_id IN (SELECT question_id FROM questions WHERE {everything} OR topic_index in ({topics}))
THEN 1 ELSE 0 END, gen_count = {q_repeat}
WHERE sessions.user_id = {user_id}'''

    #print(q)

    q2 = f'''
INSERT OR IGNORE INTO sessions (user_id, question_id, in_use_flag, gen_count)
SELECT {user_id}, questions.question_id, 1, {q_repeat}
FROM questions, sessions
WHERE questions.topic_index IN ({topics})
'''

    #print(q)
    query_db(q)
    #print(q2)
    query_db(q2)

def get_chart_data():

    data = None

    while data is None:

        if not randint(0, 2):
            correct = randint(0, 1)
            q = f'''
    SELECT answer, COUNT(answer) as county
    FROM answers 
    WHERE correct = {correct}
    AND LENGTH(answer) > 2
    GROUP BY answer
    ORDER BY county
    DESC LIMIT 10'''
            title = f"Most Popular {'Correct' if correct else 'Incorrect'} Answers"
            data = query_db(q)
        elif randint(0, 1):
            data = read_leaderboard_from_db(mode=0)[0]
            title = f"Top 25 Most Engaged Students (Total Number of Correct Answers)"
        else:
            digit = randint(0, 9)

            q = f'''SELECT users.user_id,
    SUM(CASE WHEN answers.correct = 1 THEN 1 ELSE 0 END),
    COUNT(answers.answer)
    FROM answers, users
    WHERE answers.user_id = users.user_id
    AND answers.answer != ""
    AND SUBSTRING(users.nickname, 6, 1)="{digit}"
    GROUP BY username'''
            data = query_db(q)
            title = f"% Success Rate - Students Whose Roll Number Ends In A '{digit}'"


    return {"title":title, "data":data}

def init_misnomers(user_id):
    q = f'''SELECT DISTINCT questions.gaps
    FROM questions, users, sessions
    WHERE users.user_id = {user_id}
    AND (users.hide_non_topic = 0
    OR 
    (sessions.in_use_flag = 1
    AND sessions.user_id = {user_id}
    AND questions.question_id = sessions.question_id))
    '''

    results = query_db(q)
    misnomers = []
    for row in results:
        misnomers += [word for word in row[0].split(", ")]

    shuffle(misnomers)
    return sample(list(set(misnomers)), 200)


def get_misnomers(misnomers, correct, user_id, num_hints):
    misnomers = set(sample(misnomers, num_hints))
    misnomers |= set(correct)
    misnomers = list(misnomers)
    shuffle(misnomers)
    return misnomers




def get_question_data(user_id):
    """Generates a question and updates session table"""
    q = f'''SELECT questions.question_id, questions.question, questions.gaps, sessions.gen_count
    FROM questions, sessions
    WHERE questions.question_id = sessions.question_id
    AND sessions.user_id = {user_id}
    AND sessions.in_use_flag = 1
    AND (sessions.gen_count IS NULL OR sessions.gen_count > 0)
    ORDER BY Random()
    LIMIT 1;'''

    result = query_db(q)

    if len(result) == 0 or result is None:
        return None

    question_id, question_text, gaps, count = result[0]

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
    ts = int(datetime.now().timestamp())

    q += ",".join(f'("{answer}", {score}, "{user_id}", {ts + i + 1})' for i, (answer, score) in enumerate(zip(answers, scores)))

    query_db(q)


def read_leaderboard_from_db(mode):
    """Returns overall leaderboard and last hour leaderboard"""
    count_answer_query = "SUM(answers.correct) as overall"
    if mode == 0:
        count_answer_query = "(cast(SUM(answers.correct) AS REAL) / COUNT(answers.correct)) * 100 as overall"

    q = f'''
    SELECT
       answers.user_id as user,   
       users.username,
       users.username,
       {count_answer_query}
    FROM
       answers, users
    WHERE
        answers.user_id = users.user_id
    AND
        users.opt_out = 0
    GROUP BY
        users.user_id
    HAVING
        user = answers.user_id
    ORDER BY overall DESC
    LIMIT 25'''

    overall_leaderboard = query_db(q)

    q2 = f'''
SELECT
   answers.user_id as user,
   users.username,   
   users.username,
   {count_answer_query}
FROM
   answers, users
WHERE
	answers.user_id = users.user_id
AND
    users.opt_out = 0
AND answers.time_stamp > {datetime.now().timestamp() - ONE_HOUR} 

GROUP BY
	users.user_id
HAVING
	user = answers.user_id
ORDER BY overall DESC
LIMIT 25'''

    last_hour_leaderboard = query_db(q2)

    return overall_leaderboard, last_hour_leaderboard


def save_settings_to_db(eal, non_topic, opt_out, leaderboard_mode, display_mode, highlight, user_id):
    #print("saving", display_mode, leaderboard_mode)
    leaderboard_mode = LEADERBOARD_MODES.index(leaderboard_mode)
    display_mode = DISPLAY_MODES.index(display_mode)

    q = f"""
UPDATE
    users
SET 
    eal_mode={eal},
    hide_non_topic={non_topic},
    opt_out={opt_out},
    highlight={highlight},
    leaderboard_mode={leaderboard_mode},
    display_mode={display_mode}
WHERE
    user_id = {user_id}"""
    query_db(q)



def get_settings_from_db(user_id):
    q = f"SELECT eal_mode, hide_non_topic, opt_out, leaderboard_mode, display_mode, highlight FROM users WHERE user_id = {user_id}"
    return query_db(q)

if __name__ == "__main__":

    print(get_topic_data())
