from app import app
from models import *

import dotenv
import hashlib
import json
import os

if __name__ == "__main__":

    dotenv.load_dotenv("../.env")
    with app.app_context():

        if os.environ.get("STAGE") == "dev":
            db.drop_all()
            db.create_all()

            api_key = os.environ.get("API_KEY")

            hashed_api_key = hashlib.sha256(api_key.encode("utf-8")).hexdigest()

            # add dummy data for development
            db.session.add(
                User(email="self.service.portal@xcloud.example", api_key=hashed_api_key)
            )
            db.session.add(Image(name="redhat-8.6"))
            db.session.add(Image(name="redhat-9.0"))

            db.session.add(ServerType(architecture="x86", name="linux-small"))
            db.session.add(ServerType(architecture="x86", name="linux-large"))
            db.session.add(
                ActionType(
                    name="CREATE_SERVER",
                )
            )

            db.session.add(
                ActionType(
                    name="DELETE_SERVER",
                )
            )

            db.session.add(
                ActionType(
                    name="MODIFY_SERVER",
                )
            )

            db.session.add(Datacenter(name="fra1"))

            db.session.commit()

        else:
            db.create_all()
