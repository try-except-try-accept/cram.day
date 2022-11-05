
from database import save_answers_to_db
from random import choice, randint

dummies = '''1170
1003
1052
1015
1011
1013
1014
1053
1051
1049
1176'''.split("\n")


from time import sleep

while True:
    save_answers_to_db(int(choice(dummies)), ["dummy"], [randint(0, 1)])
    sleep(randint(1, 5))
    
