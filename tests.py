#!/usr/bun/env python3

from datetime import datetime
from random import choices, randint
from string import printable
from typing import Any, Dict
from uuid import uuid1

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from main import CoffeeBag, CoffeeUse, app

client = TestClient(app)


@pytest.fixture
def mock_bag() -> CoffeeBag:
    return CoffeeBag(brand="FakeCoffee", name="Not real coffee")


@pytest.fixture
def mock_use() -> CoffeeUse:
    return CoffeeUse(bag_id="BAG-ID", datetime=datetime.now())


#### ---- Test Getters ---- ####


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200


#### ---- Test Passwords ---- ####

N_TRIES = 1


def mock_password() -> str:
    k = randint(10, 50)
    return "".join(choices(list(printable), k=k))


def test_add_new_bag_password(mock_bag: CoffeeBag):
    for _ in range(N_TRIES):
        response = client.put(
            f"/new_bag/?password={mock_password()}", json=jsonable_encoder(mock_bag)
        )
        assert response.status_code == 401
    response = client.put("/new_bag/?password=", json=jsonable_encoder(mock_bag))
    assert response.status_code == 401


def test_add_new_use_password(mock_bag: CoffeeBag):
    for _ in range(N_TRIES):
        response = client.put(
            f"/new_use/{mock_bag._key}?password={mock_password()}",
            json=jsonable_encoder(mock_bag),
        )
        assert response.status_code == 401
    response = client.put(
        f"/new_use/{mock_bag._key}?password=", json=jsonable_encoder(mock_bag)
    )
    assert response.status_code == 401


def test_deactivate_bag_password(mock_bag: CoffeeBag):
    for _ in range(N_TRIES):
        response = client.patch(
            f"/deactivate/{mock_bag._key}?password={mock_password()}",
            json=jsonable_encoder(mock_bag),
        )
        assert response.status_code == 401
    response = client.patch(
        f"/deactivate/{mock_bag._key}?password=", json=jsonable_encoder(mock_bag)
    )
    assert response.status_code == 401


def test_activate_bag_password(mock_bag: CoffeeBag):
    for _ in range(N_TRIES):
        response = client.patch(
            f"/activate/{mock_bag._key}?password={mock_password()}",
            json=jsonable_encoder(mock_bag),
        )
        assert response.status_code == 401
    response = client.patch(
        f"/activate/{mock_bag._key}?password=", json=jsonable_encoder(mock_bag)
    )
    assert response.status_code == 401


def test_update_bag_password(mock_bag: CoffeeBag):
    for _ in range(N_TRIES):
        response = client.patch(
            f"/update_bag/{mock_bag._key}?field=field&value=value&password={mock_password()}",
            json=jsonable_encoder(mock_bag),
        )
        assert response.status_code == 401
    response = client.patch(
        f"/update_bag/{mock_bag._key}?field=field&value=value&password=",
        json=jsonable_encoder(mock_bag),
    )
    assert response.status_code == 401


def test_delete_bag_password(mock_bag: CoffeeBag):
    for _ in range(N_TRIES):
        response = client.delete(
            f"/delete_bag/{mock_bag._key}?password={mock_password()}",
            json=jsonable_encoder(mock_bag),
        )
        assert response.status_code == 401
    response = client.delete(
        f"/delete_bag/{mock_bag._key}?password=",
        json=jsonable_encoder(mock_bag),
    )
    assert response.status_code == 401


def test_delete_bags_password():
    bag_ids = [str(uuid1()) for _ in range(4)]
    for _ in range(N_TRIES):
        response = client.delete(
            f"/delete_bags/?password={mock_password()}",
            json=jsonable_encoder(bag_ids),
        )
        assert response.status_code == 401
    response = client.delete(
        f"/delete_bags/?password=",
        json=jsonable_encoder(bag_ids),
    )
    assert response.status_code == 401


def test_delete_use_password(mock_use: CoffeeUse):
    for _ in range(N_TRIES):
        response = client.delete(
            f"/delete_use/{mock_use._key}?password={mock_password()}",
            json=jsonable_encoder(mock_use),
        )
        assert response.status_code == 401
    response = client.delete(
        f"/delete_use/{mock_use._key}?password=",
        json=jsonable_encoder(mock_use),
    )
    assert response.status_code == 401


def test_delete_uses_password():
    use_ids = [str(uuid1()) for _ in range(4)]
    for _ in range(N_TRIES):
        response = client.delete(
            f"/delete_uses/?password={mock_password()}",
            json=jsonable_encoder(use_ids),
        )
        assert response.status_code == 401
    response = client.delete(
        f"/delete_uses/?password=",
        json=jsonable_encoder(use_ids),
    )
    assert response.status_code == 401
