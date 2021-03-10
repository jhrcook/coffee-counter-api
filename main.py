#!/usr/bin/env python3

import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from deta import Deta
from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
from passlib.context import CryptContext
from pydantic import BaseModel

from keys import PROJECT_KEY

HASHED_PASSWORD = "$2b$12$VOGTaA8tXdYoAU4Js6NBXO9uL..rXITV.WMiF/g8MEmCtdoMjLkOK"
pwd_context = CryptContext(schemes=["bcrypt"])

app = FastAPI()


#### ---- Datebases ---- ####

deta = Deta(PROJECT_KEY)  # no key needed with using Deta Micro
coffee_bag_db = deta.Base("coffee_bag_db")
coffee_use_db = deta.Base("coffee_use_db")


class CoffeeBag(BaseModel):
    brand: str
    name: str
    weight: float = 340.0
    start: Optional[date] = date.today()
    finish: Optional[date] = None


class CoffeeUse(BaseModel):
    bag_id: str
    datetime: datetime


def get_all_coffee_info() -> List[Dict[str, Any]]:
    return list(coffee_bag_db.fetch())[0]


def coffee_bag_list() -> List[CoffeeBag]:
    return [CoffeeBag(**info) for info in get_all_coffee_info()]


def coffee_bag_dict() -> Dict[str, CoffeeBag]:
    return {info["key"]: CoffeeBag(**info) for info in get_all_coffee_info()}


#### ---- Security ---- ####


def verify_password(password: str) -> bool:
    return pwd_context.verify(password, HASHED_PASSWORD)


#### ---- Start Page ---- ####


@app.get("/")
async def root():
    return {"message": "Coffee Counter API"}


#### ---- Getters ---- ####


@app.get("/bags")
def get_bags():
    return coffee_bag_dict()


@app.get("/bag/{bag_id}")
def get_bag_info(bag_id: str):
    bag = coffee_bag_db.get(bag_id)
    if bag is None:
        return status.HTTP_400_BAD_REQUEST
    return CoffeeBag(**bag)


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


# @app.get("/uses")
# def get_uses(n_last: Optional[int] = None, bag_ids: Optional[List[str]] = None):
#     coffee_uses: List[CoffeeUse] = list(coffee_use_db.values())

#     if not bag_ids is None:
#         coffee_uses = [u for u in coffee_uses if u.bag_id in bag_ids]

#     coffee_uses.sort(key=lambda x: x.datetime)
#     if not n_last is None:
#         return coffee_uses[-n_last:]
#     return coffee_uses


#### ---- Setters ---- ####


@app.put("/new_bag/")
def add_new_bag(bag: CoffeeBag, password: str = "STAND_IN"):
    if not verify_password(password):
        # return status.HTTP_401_UNAUTHORIZED
        print("password verification not yet implemented")

    coffee_bag_db.put(jsonable_encoder(bag))
    return bag


@app.delete("/delete_bag/")
def delete_bag(bag_ids: List[str], password: str = "STAND_IN"):
    if not verify_password(password):
        # return status.HTTP_401_UNAUTHORIZED
        print("password verification not yet implemented")

    for id in bag_ids:
        coffee_bag_db.delete(id)


@app.delete("/delete_all_bags/")
def delete_all_bags(password: str = "STAND_IN"):
    if not verify_password(password):
        # return status.HTTP_401_UNAUTHORIZED
        print("password verification not yet implemented")

    for bag in coffee_bag_db.fetch():
        coffee_bag_db.delete(bag["key"])


# @app.put("/new_use/")
# def add_new_use(
#     bag_id: str, when: datetime = datetime.now(), password: str = "STAND_IN"
# ):
#     if not verify_password(password):
#         # return status.HTTP_401_UNAUTHORIZED
#         print("password verification not yet implemented")

#     if not bag_id in coffee_bag_db.keys():
#         return status.HTTP_400_BAD_REQUEST

#     new_coffee_use = CoffeeUse(bag_id=bag_id, datetime=when)
#     use_id = "use" + str(len(coffee_use_db) + 1)
#     coffee_use_db[use_id] = new_coffee_use
#     return new_coffee_use


# @app.put("/finish_bag/")
# def finished_bag(bag_id: str, when: date = date.today(), password: str = "STAND_IN"):
#     if not verify_password(password):
#         # return status.HTTP_401_UNAUTHORIZED
#         print("passwords not required, yet")

#     try:
#         bag = coffee_bag_db[bag_id]
#     except:
#         return status.HTTP_400_BAD_REQUEST

#     if bag.finish is None:
#         bag.finish = when
#         coffee_bag_db[bag_id] = bag
#         return bag
#     else:
#         return status.HTTP_400_BAD_REQUEST


# @app.patch("/update_bag/")
# def update_bag(bag_id: str, bag: CoffeeBag, password: str = ""):
#     if not verify_password(password):
#         # return status.HTTP_401_UNAUTHORIZED
#         print("password verification not yet implemented")

#     if bag_id in coffee_bag_db.keys():
#         coffee_bag_db[bag_id] = bag
#         return bag
#     else:
#         return status.HTTP_400_BAD_REQUEST
