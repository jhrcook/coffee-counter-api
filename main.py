#!/usr/bin/env python3

from datetime import date
from secrets import PROJECT_KEY
from typing import Any, Dict, List, Optional

from deta import Deta
from fastapi import FastAPI
from passlib.context import CryptContext

HASHED_PASSWORD = "$2b$12$VOGTaA8tXdYoAU4Js6NBXO9uL..rXITV.WMiF/g8MEmCtdoMjLkOK"
pwd_context = CryptContext(schemes=["bcrypt"])

# deta = Deta(PROJECT_KEY)
# coffee_bag_db = deta.Base("coffee_bag_db")
# coffee_use_db = deta.Base("coffee_use_db")

app = FastAPI()

#### ---- Mock databases ---- ####

coffee_bag_db = {
    "bag1": {
        "brand": "BRCC",
        "name": "Flying Elk",
        "weight": 340,
        "start": date(year=2021, month=2, day=19),
        "finish": None,
    },
    "bag2": {
        "brand": "BRCC",
        "name": "Beyond Black",
        "weight": 340,
        "start": date(year=2021, month=2, day=1),
        "finish": date(year=2021, month=3, day=7),
    },
}

coffee_use_db = {
    "use1": {"bag": "bag1", "date": date(2021, 2, 21)},
    "use2": {"bag": "bag1", "date": date(2021, 2, 22)},
    "use3": {"bag": "bag1", "date": date(2021, 2, 22)},
    "use4": {"bag": "bag1", "date": date(2021, 2, 25)},
    "use5": {"bag": "bag1", "date": date(2021, 3, 5)},
    "use6": {"bag": "bag2", "date": date(2021, 2, 5)},
    "use7": {"bag": "bag2", "date": date(2021, 2, 10)},
    "use8": {"bag": "bag2", "date": date(2021, 2, 15)},
    "use9": {"bag": "bag2", "date": date(2021, 3, 3)},
    "use10": {"bag": "bag2", "date": date(2021, 3, 5)},
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
    return coffee_bag_db[bag_id]


@app.get("/uses")
def get_uses(n_last: Optional[int] = None):
    coffee_uses: List[Dict[str, Any]] = list(coffee_use_db.values())
    coffee_uses.sort(key=lambda x: x["date"])
    if not n_last is None:
        return coffee_uses[-n_last:]
    return coffee_uses
