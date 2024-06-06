from dataclasses import dataclass
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped

import datetime
import os

db = SQLAlchemy()


def get_connection_string():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    return "sqlite:///" + os.path.join(base_dir, "database.db")


class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False
    )


@dataclass
class User(Base):
    email = db.Column(db.String(320), unique=True, nullable=False)
    api_key = db.Column(db.String(64), unique=True, nullable=False)
    api_request_count = db.Column(db.Integer, default=0)


@dataclass
class Action(Base):
    id: int

    started_at: str = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    finished_at: str = db.Column(db.DateTime)

    progress: int = db.Column(db.Integer(), default=0)

    status: str = db.Column(db.String(32), default="QUEUED", nullable=False)

    is_finished: bool = db.Column(db.Boolean(), default=False, nullable=False)

    server_id = db.Column(db.ForeignKey("server.id"), nullable=False)
    action_type_id = db.Column(db.ForeignKey("action_type.id"), nullable=False)

    server = db.relationship("Server", backref="actions", lazy=True)


@dataclass
class ActionType(Base):
    name: str = db.Column(db.String(32), nullable=False)

    actions = db.relationship("Action", backref="action_type", lazy=True)


@dataclass
class Image(Base):
    id: int
    name: str = db.Column(db.Text(), nullable=False)

    created_at: datetime.datetime


@dataclass
class Datacenter(Base):
    id: int
    name: str = db.Column(db.Text(), nullable=False)

    created_at: datetime.datetime


@dataclass
class ServerType(Base):
    id: int
    architecture: str = db.Column(db.Text(), nullable=False)
    is_deprecated: bool = db.Column(db.Boolean(), default=False, nullable=False)
    name: str = db.Column(db.Text(), nullable=False)


@dataclass
class Server(Base):
    id: int
    name: str = db.Column(db.Text(), nullable=False)

    ipv4_address: str = db.Column(db.String(15))
    is_deprovisioned: bool = db.Column(db.Boolean(), default=False, nullable=False)

    image_id = db.Column(db.ForeignKey("image.id"), nullable=False)
    datacenter_id = db.Column(db.ForeignKey("datacenter.id"), nullable=False)
    server_type_id = db.Column(db.ForeignKey("server_type.id"), nullable=False)
    user_id = db.Column(db.ForeignKey("user.id"), nullable=False)

    image: Mapped[Image] = db.relationship("Image", lazy="joined")
    server_type: Mapped[ServerType] = db.relationship("ServerType", lazy="joined")
    datacenter: Mapped[Datacenter] = db.relationship("Datacenter", lazy="joined")
