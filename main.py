#!/usr/bin/env python3

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from deta import Deta
from fastapi import FastAPI, status
from passlib.context import CryptContext
from pydantic import BaseModel

# from keys import PROJECT_KEY

HASHED_PASSWORD = "$2b$12$VOGTaA8tXdYoAU4Js6NBXO9uL..rXITV.WMiF/g8MEmCtdoMjLkOK"
pwd_context = CryptContext(schemes=["bcrypt"])

# deta = Deta()  # no key needed with using Deta Micro
# coffee_bag_db = deta.Base("coffee_bag_db")
# coffee_use_db = deta.Base("coffee_use_db")

app = FastAPI()

#### ---- Mock databases ---- ####


class CoffeeBag(BaseModel):
    brand: str
    name: str
    weight: float = 340.0
    start: Optional[date] = date.today()
    finish: Optional[date] = None


class CoffeeUse(BaseModel):
    bag_id: str
    datetime: datetime


coffee_bag_db = {
    "bag1": CoffeeBag(
        brand="BRCC",
        name="Flying Elk",
        weight=340.0,
        start=date(year=2021, month=2, day=19),
    ),
    "bag2": CoffeeBag(
        brand="BRCC",
        name="Beyond Black",
        weight=340.0,
        start=date(year=2021, month=2, day=1),
        finish=date(year=2021, month=3, day=7),
    ),
}

coffee_use_db = {
    "use1": CoffeeUse(bag_id="bag1", datetime=datetime(2021, 2, 21)),
    "use2": CoffeeUse(bag_id="bag1", datetime=datetime(2021, 2, 22)),
    "use3": CoffeeUse(bag_id="bag1", datetime=datetime(2021, 2, 22)),
    "use4": CoffeeUse(bag_id="bag1", datetime=datetime(2021, 2, 25)),
    "use5": CoffeeUse(bag_id="bag1", datetime=datetime(2021, 3, 5)),
    "use6": CoffeeUse(bag_id="bag2", datetime=datetime(2021, 2, 5)),
    "use7": CoffeeUse(bag_id="bag2", datetime=datetime(2021, 2, 10)),
    "use8": CoffeeUse(bag_id="bag2", datetime=datetime(2021, 2, 15)),
    "use9": CoffeeUse(bag_id="bag2", datetime=datetime(2021, 3, 3)),
    "use10": CoffeeUse(bag_id="bag2", datetime=datetime(2021, 3, 5)),
}


def verify_password(password: str) -> bool:
    return pwd_context.verify(password, HASHED_PASSWORD)


#### ---- Start Page ---- ####


@app.get("/")
async def root():
    return {"message": "Coffee Counter API"}


#### ---- Getters ---- ####


@app.get("/bags")
def get_bags():
    return coffee_bag_db


@app.get("/bag/{bag_id}")
def get_bag_info(bag_id: str):
    try:
        bag = coffee_bag_db[bag_id]
    except:
        return status.HTTP_400_BAD_REQUEST
    return bag


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
    bags = list(coffee_bag_db.values())
    bags = [bag for bag in bags if bag.finish is None and not bag.start is None]
    sort_coffee_bags(bags)

    if not n_last is None:
        bags = bags[-n_last:]

    return bags


@app.get("/uses")
def get_uses(n_last: Optional[int] = None, bag_ids: Optional[List[str]] = None):
    coffee_uses: List[CoffeeUse] = list(coffee_use_db.values())

    if not bag_ids is None:
        coffee_uses = [u for u in coffee_uses if u.bag_id in bag_ids]

    coffee_uses.sort(key=lambda x: x.datetime)
    if not n_last is None:
        return coffee_uses[-n_last:]
    return coffee_uses


#### ---- Setters ---- ####


@app.put("/new_bag/")
def add_new_bag(bag: CoffeeBag, password: str = "STAND_IN"):
    if not verify_password(password):
        # return status.HTTP_401_UNAUTHORIZED
        print("password verification not yet implemented")

    bag_id = "bag" + str(len(coffee_bag_db) + 1)
    coffee_bag_db[bag_id] = bag
    return bag


@app.put("/new_use/")
def add_new_use(
    bag_id: str, when: datetime = datetime.now(), password: str = "STAND_IN"
):
    if not verify_password(password):
        # return status.HTTP_401_UNAUTHORIZED
        print("password verification not yet implemented")

    if not bag_id in coffee_bag_db.keys():
        return status.HTTP_400_BAD_REQUEST

    new_coffee_use = CoffeeUse(bag_id=bag_id, datetime=when)
    use_id = "use" + str(len(coffee_use_db) + 1)
    coffee_use_db[use_id] = new_coffee_use
    return new_coffee_use


@app.put("/finish_bag/")
def finished_bag(bag_id: str, when: date = date.today(), password: str = "STAND_IN"):
    if not verify_password(password):
        # return status.HTTP_401_UNAUTHORIZED
        print("passwords not required, yet")

    try:
        bag = coffee_bag_db[bag_id]
    except:
        return status.HTTP_400_BAD_REQUEST

    if bag.finish is None:
        bag.finish = when
        coffee_bag_db[bag_id] = bag
        return bag
    else:
        return status.HTTP_400_BAD_REQUEST


@app.patch("/update_bag/")
def update_bag(bag_id: str, bag: CoffeeBag, password: str = ""):
    if not verify_password(password):
        # return status.HTTP_401_UNAUTHORIZED
        print("password verification not yet implemented")

    if bag_id in coffee_bag_db.keys():
        coffee_bag_db[bag_id] = bag
        return bag
    else:
        return status.HTTP_400_BAD_REQUEST
