from app import app
from models import *
from loguru import logger

import random
import time


def execute_actions():
    actions = db.session.query(Action).filter(Action.status == "QUEUED").limit(10).all()

    for action in actions:

        if action.action_type.name == "CREATE_SERVER":
            # transform resource attributes to input for legacy APIs
            # e.g. yaml

            # trigger actual deployment workflow, playbook, etc...

            logger.info(f"triggering legacy deployment for {action.server.name}")

        action.status = "RUNNING"
        db.session.add(action)


def check_actions():
    actions = (
        db.session.query(Action).filter(Action.status == "RUNNING").limit(10).all()
    )

    for action in actions:

        # HERE: check legacy API (e.g. VMware vRealize Automation) for progress and update related infos, e.g. ipv4_address

        # for demo purposes we finish the actions after 10 minutes
        time_limit = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            minutes=10
        )

        # use real conditions here
        if action.started_at.replace(tzinfo=datetime.timezone.utc) < time_limit:
            action.progress = 100
            action.status = "COMPLETED"
            action.is_finished = True
            action.server.ipv4_address = "10.10.10.10"

            action.finished_at = datetime.datetime.now(datetime.timezone.utc)

            logger.info(f"setting action with id {action.id} to status {action.status}")
        else:
            action.progress = random.randint(0, 100)

        db.session.add(action)

    db.session.commit()


if __name__ == "__main__":
    with app.app_context():

        while True:

            # this is a very simple example
            # feel free to blow this out of proportion with celery, kafka , etc... but remember: simplicity is key ;)
            execute_actions()
            check_actions()

            time.sleep(0.5)
