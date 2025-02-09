from requests import get
from time import sleep
while True:

    get("https://cramdotday.herokuapp.com/answer_sync")
    sleep(60)