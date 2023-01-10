import datetime
import json
import os
import time

import requests
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import DataError
from config import *

pid = os.getpid()


def chunkify(lst: list, m=None, n=None) -> list:
    """n = 3000, list gets split into 3000 items per chunk, m = 20, list gets split into 20 chunks"""
    if n:
        return [lst[x:x + n] for x in range(0, len(lst), n)]
    return [lst[i::m] for i in range(m)]


def log_printer(*args, sep=" ", end="", **kwargs) -> None:
    joined_string = sep.join([str(arg) for arg in args])
    print(str(pid) + ' : ' + str(datetime.datetime.now()) + ' : ' + joined_string + "\n", sep=sep, end=end, **kwargs)


def generate_postgres(__postgres_database=POSTGRES_DATABASE):
    engine = create_engine(f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}')
    Session = sessionmaker(bind=engine)
    return Session()


def postgres_hybrid_insert(dataset: list, class_name, on_conflict: bool = True) -> None:
    if dataset:
        session = generate_postgres()
        for data in chunkify(dataset, n=500):
            if on_conflict:
                insert_query = insert(class_name).values(data).on_conflict_do_nothing()
            else:
                insert_query = insert(class_name).values(data)
            session.execute(insert_query)
            session.commit()


def vitispro_slack_notification(message, username="Scraper Notification", emoji=":ghost:"):
    data = {
        "text": str(message),
        "username": username,
        "icon_emoji": emoji
    }
    response = requests.post(url='https://hooks.slack.com/services/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',
                             data=json.dumps(data),
                             headers={'Content-Type': 'application/json'})
    log_printer(f'Slack notification sent, status code: {response.status_code}')


def send_slack_notification(message, username="Scraper Notification", status=True):
    payload = {"text": message, "username": username, "channel": "C03HZ1VHDAM"}

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer xoxb-3585952876390-3771340364006-gNQeF6wDoLhvNmFLGbBwGdWC' if status else 'Bearer xoxb-3585952876390-3683229725188-VnCeEgmsiYe37SfoE6zEMp6x'
    }
    response = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload)
    log_printer(f'Slack notification sent, status code: {response.status_code}')

    vitispro_slack_notification(message, username)


def notification_lite(message, username="I smell like ass", emoji=":smiling_face_with_tear:"):
    payload = {"text": message, "username": username, "icon_emoji": emoji, "channel": "C03PKLJ0ZMW"}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer xoxb-3585952876390-3771340364006-gNQeF6wDoLhvNmFLGbBwGdWC'
    }
    response = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload)
    log_printer(f'Slack notification sent, status code: {response.status_code}')


def requests_get(url: str, **kwargs):
    while True:
        try:
            res = requests.get(url, **kwargs, timeout=60)
            log_printer(f'status_code: {res.status_code}, RTT: {res.elapsed.total_seconds()}, url: {res.url}')
            if res.status_code in (404, 500, 422):
                return
            else:
                res.raise_for_status()
                return res
        except requests.exceptions.RequestException:
            log_printer(f'sleeping 60 seconds, url: {url}')
            time.sleep(60)
            pass


def requests_post(url: str, **kwargs):
    while True:
        try:
            res = requests.post(url, **kwargs, timeout=60)
            log_printer(f'status_code: {res.status_code}, RTT: {res.elapsed.total_seconds()}, url: {res.url}, payload: {res.request.body}')
            if res.status_code in (404, 500, 422):
                return
            else:
                res.raise_for_status()
                return res
        except requests.exceptions.RequestException:
            log_printer(f'sleeping 60 seconds, url: {url}')
            time.sleep(60)
            pass
