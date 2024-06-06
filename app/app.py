import datetime
import dotenv
import hashlib
import json
import os

from loguru import logger
from flask import Flask, g, make_response, jsonify, request
from flask.json.provider import DefaultJSONProvider

from functools import wraps
from models import *

dotenv.load_dotenv("../.env")


class UpdatedJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            # return o.replace(tzinfo=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            # this enforces isoformat 8601 on all dates
            return o.replace(tzinfo=datetime.timezone.utc).isoformat()
        return super().default(o)


app = Flask(__name__)
app.json = UpdatedJSONProvider(app)

app.config["SQLALCHEMY_DATABASE_URI"] = get_connection_string()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

if int(os.environ.get("SQL_DEBUG", 0)) == 1:
    app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)

logger.level("DEBUG", color="<light-green>")


def authenticated(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not "authorization" in request.headers:
            return make_response(
                jsonify({"error": f"Missing authorization header"}), 403
            )

        auth_header = request.headers.get("authorization", "")
        api_key = auth_header.split(" ")[1]

        # sha256 is faster than bcrypt and enough for long api tokens
        hashed_api_key = hashlib.sha256(api_key.encode("utf-8")).hexdigest()

        user = db.session.query(User).filter(User.api_key == hashed_api_key).first()

        if user is None:
            return make_response(jsonify({"error": "Invalid API Token"}), 403)

        user.api_request_count = user.api_request_count + 1
        db.session.add(user)
        db.session.commit()

        g.user = user

        # TODO: use FLASK_DEBUG and logger.debug()
        if os.environ.get("STAGE", "").upper() == "DEV":

            tmp_headers = dict(request.headers)
            tmp_headers["Authorization"] = "Bearer <REDACTED>"

            message = (
                "\n"
                + request.method
                + "\t"
                + request.url
                + "\n\n"
                + json.dumps(tmp_headers, indent=4)
            )

            if request.is_json:
                try:
                    message += "\n\n" + json.dumps(request.get_json(), indent=4)
                except:
                    pass

            logger.debug(message)

        return f(*args, **kwargs)

    return decorated_function


@app.after_request
def after(response):
    if os.getenv("STAGE", "").upper() == "DEV":
        message = (
            "\n"
            + json.dumps(dict(response.headers), indent=4)
            + "\n\n\n"
            + response.get_data(as_text=True)
        )
        logger.info(message)
        return response


@app.route("/actions/<id>", methods=["GET"])
@authenticated
def get_action_by_id(id):
    action = db.session.get(Action, id)

    if action is None:
        return make_response(
            jsonify(
                {
                    "error": f"action with {id} not found",
                }
            ),
            404,
        )

    return make_response(
        jsonify(
            {
                "action": action,
            }
        ),
        200,
    )


@app.route("/servers/<id>", methods=["GET"])
@authenticated
def get_server(id):
    server = db.session.get(Server, id)

    if server is None:
        return make_response(
            jsonify(
                {
                    "error": f"server with {id} not found",
                }
            ),
            404,
        )

    if not server.user_id == g.user.id:
        return make_response(
            jsonify(
                {
                    "error": f"server with {id} does not belong to you",
                }
            ),
            403,
        )

    return make_response(
        jsonify(
            {
                "server": server,
            }
        ),
        200,
    )


@app.route("/servers", methods=["POST"])
@authenticated
def create_server():
    action_type = (
        db.session.query(ActionType).filter(ActionType.name == "CREATE_SERVER").first()
    )

    server_type = (
        db.session.query(ServerType)
        .filter(ServerType.name == request.json["server_type"]["name"])
        .first()
    )

    datacenter = (
        db.session.query(Datacenter)
        .filter(Datacenter.name == request.json["datacenter"]["name"])
        .first()
    )

    image = (
        db.session.query(Image)
        .filter(Image.name == request.json["image"]["name"])
        .first()
    )

    server_name = request.json["name"]

    server = Server(
        datacenter_id=datacenter.id,
        image_id=image.id,
        name=server_name,
        server_type_id=server_type.id,
        user_id=g.user.id,
    )

    db.session.add(server)
    db.session.commit()

    action = Action(
        server_id=server.id,
        action_type_id=action_type.id,
    )
    db.session.add(action)
    db.session.commit()

    return make_response(
        jsonify(
            {
                "action": action,
                "next_actions": [],
                "server": server,
            }
        ),
        200,
    )


@app.route("/servers/<id>", methods=["DELETE"])
@authenticated
def delete_server(id):
    server = db.session.get(Server, id)

    if server is None:
        return make_response(
            jsonify(
                {
                    "error": f"server with {id} not found",
                }
            ),
            404,
        )

    if not server.user_id == g.user.id:
        return make_response(
            jsonify(
                {
                    "error": f"server with {id} does not belong to you",
                }
            ),
            403,
        )

    server.is_deprovisioned = True
    db.session.add(server)
    db.session.commit()

    action_type = (
        db.session.query(ActionType).filter(ActionType.name == "DELETE_SERVER").first()
    )

    action = Action(
        command=action_type.name,
        server_id=server.id,
        action_type_id=action_type.id,
    )
    db.session.add(action)
    db.session.commit()

    return make_response(
        jsonify(
            {
                "action": action,
                "next_actions": [],
                "server": server,
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1337, debug=True)
