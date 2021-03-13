#!/usr/bin/env python3

import uuid
from datetime import date, datetime
from enum import Enum
from math import ceil
from typing import Any, Dict, List, Optional

from deta import Deta
from deta.base import Base
from fastapi import FastAPI, Query, status
from fastapi.encoders import jsonable_encoder
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from pydantic.fields import PrivateAttr

from keys import PROJECT_KEY

HASHED_PASSWORD = "$2b$12$VOGTaA8tXdYoAU4Js6NBXO9uL..rXITV.WMiF/g8MEmCtdoMjLkOK"
pwd_context = CryptContext(schemes=["bcrypt"])

app = FastAPI()

EPOCH = datetime.utcfromtimestamp(0)

#### ---- Datebases ---- ####

deta = Deta(PROJECT_KEY)  # no key needed with using Deta Micro
# coffee_bag_db = deta.Base("coffee_bag_db")
# coffee_use_db = deta.Base("coffee_use_db")
# meta_db = deta.Base("meta_db")

coffee_bag_db = deta.Base("coffee_bag_db-TEST")
coffee_use_db = deta.Base("coffee_use_db-TEST")
meta_db = deta.Base("meta_db-TEST")


#### ---- Models ---- ####


def make_key() -> str:
    return str(uuid.uuid4())


class CoffeeBag(BaseModel):
    brand: str
    name: str
    weight: float = 340.0
    start: Optional[date] = date.today()
    finish: Optional[date] = None
    key: Optional[str] = Field(default_factory=make_key)


def unix_time_millis(dt: datetime = datetime.now()) -> float:
    return (dt - EPOCH).total_seconds() * 1000.0


class CoffeeUse(BaseModel):
    bag_id: str
    datetime: datetime
    key: Optional[str] = Field(default_factory=make_key)
    _seconds: float = PrivateAttr(0)

    def __init__(self, **data):
        super().__init__(**data)
        self._seconds = unix_time_millis(self.datetime)


datetime(2021, 1, 1, 1, 1, 1)


#### ---- Database interface helpers ---- ####


def convert_info_to_bag(info: Dict[str, Any]) -> CoffeeBag:
    return CoffeeBag(**info)


def convert_bag_to_info(bag: CoffeeBag) -> Dict[str, Any]:
    return jsonable_encoder(bag)


def convert_info_to_use(info: Dict[str, Any]) -> CoffeeUse:
    return CoffeeUse(**info)


def convert_use_to_info(use: CoffeeUse) -> Dict[str, Any]:
    return jsonable_encoder(use)


def get_all_detabase_info(db: Base, n_items: int):
    n_buffer = 100
    n_pages = ceil(n_items / n_buffer) + 1  # add one just in case

    pages = db.fetch(query=None, buffer=n_buffer, pages=n_pages)
    info: List[Dict[str, Any]] = []
    for page in pages:
        info += page
    return info


def get_all_coffee_bag_info() -> List[Dict[str, Any]]:
    num_bags = meta_db.get(key=META_DB_KEY)[MetaDataField.bag_count]
    return get_all_detabase_info(coffee_bag_db, n_items=num_bags)


def coffee_bag_list() -> List[CoffeeBag]:
    return [convert_info_to_bag(info) for info in get_all_coffee_bag_info()]


def get_all_coffee_use_info() -> List[Dict[str, Any]]:
    num_uses = meta_db.get(key=META_DB_KEY)[MetaDataField.use_count]
    return get_all_detabase_info(coffee_use_db, n_items=num_uses)


#### ---- Meta DB ---- ####

META_DB_KEY = "KEY"


class MetaDataField(str, Enum):
    bag_count = "bag_count"
    use_count = "use_count"


def increment_meta_count(field: str, by: int):
    try:
        meta_db.update({field: meta_db.util.increment(by)}, key=META_DB_KEY)
    except:
        meta_db.update({field: by}, key=META_DB_KEY)
    return None


def increment_coffee_bag(by: int = 1):
    increment_meta_count(MetaDataField.bag_count, by=by)


def increment_coffee_use(by: int = 1):
    increment_meta_count(MetaDataField.use_count, by=by)


def reset_coffee_bag_count():
    meta_db.update({MetaDataField.bag_count: 0}, key=META_DB_KEY)


def reset_coffee_use_count():
    meta_db.update({MetaDataField.use_count: 0}, key=META_DB_KEY)


#### ---- Security ---- ####


def verify_password(password: str) -> bool:
    return pwd_context.verify(password, HASHED_PASSWORD)


#### ---- Start Page ---- ####


@app.get("/")
async def root():
    return {"message": "Coffee Counter API"}


#### ---- Getters ---- ####


@app.get("/bags/")
def get_bags():
    return coffee_bag_list()


@app.get("/number_of_bags/")
def get_number_of_bags() -> int:
    return meta_db.get(META_DB_KEY)[MetaDataField.bag_count]


@app.get("/bag/{bag_id}")
def get_bag_info(bag_id: str):
    bag_info = coffee_bag_db.get(bag_id)
    if bag_info is None:
        return status.HTTP_400_BAD_REQUEST
    return convert_info_to_bag(bag_info)


def sort_coffee_bags(bags: List[CoffeeBag]):
    def f(b: CoffeeBag) -> date:
        if b.start is None:
            return date.today()
        else:
            return b.start

    bags.sort(key=f)
    return None


@app.get("/active_bags/")
def get_active_bags(n_last: Optional[int] = None):
    bags = coffee_bag_list()
    bags = [bag for bag in bags if bag.finish is None and not bag.start is None]
    sort_coffee_bags(bags)

    if not n_last is None:
        bags = bags[-n_last:]

    return bags


@app.get("/uses/")
def get_uses(n_last: int = Query(100, le=10000), bag_id: Optional[str] = None):
    buffer_size = 300
    pages = ceil(n_last / buffer_size)
    uses: List[CoffeeUse] = []

    if bag_id is None:
        query = None
    else:
        query = {"bag_id": bag_id}

    for page in coffee_use_db.fetch(query=query, buffer=300, pages=pages):
        for use_info in page:
            uses.append(convert_info_to_use(use_info))

    uses.sort(key=lambda x: x.datetime)

    if len(uses) < n_last:
        return uses
    else:
        return uses[-n_last:]


@app.get("/number_of_uses/")
def get_number_of_uses() -> int:
    return meta_db.get(META_DB_KEY)[MetaDataField.use_count]


#### ---- Setters ---- ####


@app.put("/new_bag/")
def add_new_bag(bag: CoffeeBag, password: str):
    if not verify_password(password):
        return status.HTTP_401_UNAUTHORIZED

    try:
        coffee_bag_db.put(convert_bag_to_info(bag))
        increment_coffee_bag(1)
        return bag
    except:
        return status.HTTP_500_INTERNAL_SERVER_ERROR


@app.put("/new_use/{bag_id}")
def add_new_use(bag_id: str, password: str, when: datetime = datetime.now()):
    if not verify_password(password):
        return status.HTTP_401_UNAUTHORIZED

    bag_info = coffee_bag_db.get(bag_id)
    if bag_info is None:
        return status.HTTP_400_BAD_REQUEST

    new_coffee_use = CoffeeUse(bag_id=bag_id, datetime=when)

    try:
        coffee_use_db.put(convert_use_to_info(new_coffee_use))
        increment_coffee_use(1)
        return new_coffee_use
    except:
        return status.HTTP_500_INTERNAL_SERVER_ERROR


@app.patch("/finish_bag/{bag_id}")
def finished_bag(bag_id: str, password: str, when: date = date.today()):
    if not verify_password(password):
        return status.HTTP_401_UNAUTHORIZED

    bag_info = coffee_bag_db.get(key=bag_id)
    if bag_info is None:
        return status.HTTP_400_BAD_REQUEST

    if bag_info["finish"] is None:
        bag_info["finish"] = when
        coffee_bag_db.update(
            updates={"finish": jsonable_encoder(when)}, key=bag_info["key"]
        )
        return convert_info_to_bag(bag_info)
    else:
        return status.HTTP_400_BAD_REQUEST


@app.patch("/update_bag/{bag_id}")
def update_bag(bag_id: str, field: str, value: Any, password: str):
    if not verify_password(password):
        return status.HTTP_401_UNAUTHORIZED

    if field == "key":
        # Cannot change "key" field.
        return status.HTTP_400_BAD_REQUEST

    bag_info = coffee_bag_db.get(bag_id)
    if bag_info is None:
        # ID not found.
        return status.HTTP_400_BAD_REQUEST

    if not field in bag_info.keys():
        # Not a viable field in CoffeeBag model.
        return status.HTTP_400_BAD_REQUEST

    bag_info[field] = value
    try:
        bag = convert_info_to_bag(bag_info)
    except:
        # Error during data validation.
        # Data is of wrong type (provide more feedback to user)
        return status.HTTP_400_BAD_REQUEST

    coffee_bag_db.update({field: value}, key=bag_id)
    return bag


def _delete_coffee_bag(bag_id: str):
    if not coffee_bag_db.get(bag_id) is None:
        coffee_bag_db.delete(bag_id)
        increment_coffee_bag(by=-1)


@app.delete("/delete_bag/{bag_id}")
def delete_bag(bag_id: str, password: str):
    if not verify_password(password):
        return status.HTTP_401_UNAUTHORIZED

    _delete_coffee_bag(bag_id=bag_id)


@app.delete("/delete_bags/")
def delete_bags(bag_ids: List[str], password: str):
    if not verify_password(password):
        return status.HTTP_401_UNAUTHORIZED

    for id in bag_ids:
        _delete_coffee_bag(bag_id=id)


@app.delete("/delete_all_bags/")
def delete_all_bags(password: str):
    if not verify_password(password):
        return status.HTTP_401_UNAUTHORIZED

    for bag_info in get_all_coffee_bag_info():
        coffee_bag_db.delete(bag_info["key"])
    reset_coffee_bag_count()


def _delete_coffee_use(id: str):
    if not coffee_use_db.get(id) is None:
        coffee_use_db.delete(id)
        increment_coffee_use(by=-1)


@app.delete("/delete_use/{id}")
def delete_use(id: str, password: str):
    if not verify_password(password):
        return status.HTTP_401_UNAUTHORIZED

    _delete_coffee_use(id)


@app.delete("/delete_uses/")
def delete_uses(ids: List[str], password: str):
    if not verify_password(password):
        return status.HTTP_401_UNAUTHORIZED

    for id in ids:
        _delete_coffee_use(id)


@app.delete("/delete_all_uses/")
def delete_all_uses(password: str):
    if not verify_password(password):
        return status.HTTP_401_UNAUTHORIZED

    for use_info in get_all_coffee_use_info():
        coffee_use_db.delete(use_info["key"])
    reset_coffee_use_count()
