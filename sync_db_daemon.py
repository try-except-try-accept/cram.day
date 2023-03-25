from database import get_last_n_answers, sync_answer_data, load_gsheet
from config import ONE_MIN
from time import sleep
from datetime import datetime

in_session = False

while True:

    last_answers = get_last_n_answers(10)

    ## get last 10 answers
    ts = int(datetime.now().timestamp())
    within_last_minute = all(ts - ONE_MIN <= answer[0] <= ts for answer in last_answers)
    
    print("Current time is", ts)
    print("Last 10 answers took place at", last_answers)

    if within_last_minute and not in_session:
    ## if in most recent minute and session flag is false

        ## in session flag set to true
        in_session = True

        ## load answer data from spreadsheet
        print("user activity detected - load old answer data")
        sync_answer_data(load_gsheet())

    ## if not in most recent minute and session flag is true
    elif not within_last_minute and in_session:

        ## in session flag set to false
        in_session = False

        ## write answer data to spreadsheet
        print("user activity ended - save new answer data")
        sync_answer_data(load_gsheet())

    sleep(60)