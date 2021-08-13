"""Test the coffee counting API."""

import math
from datetime import date, datetime
from random import random
from typing import Any, Dict, List

import factory
import pytest
from faker import Faker
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from hypothesis import given
from hypothesis import strategies as st

import main
from main import CoffeeBag, CoffeeUse, app

main.PROJECT_KEY = ""

client = TestClient(app)


#### ---- Fake data ---- ####

fake = Faker()
fake.seed_instance(123)


class CoffeeBagFactory(factory.Factory):
    class Meta:
        model = CoffeeBag

    brand = fake.name()
    name = fake.name()
    weight = fake.pyfloat()
    start = fake.date()
    finish = fake.date()
    active = fake.boolean()


class CoffeeUseFactory(factory.Factory):
    class Meta:
        model = CoffeeUse

    bag_id = fake.sha1()
    datetime = fake.date_time()


def mock_coffee_bag_info(*args, **kwargs) -> List[Dict[str, Any]]:
    return [CoffeeBagFactory().dict() for _ in range(5)]


def mock_coffee_use_info(*args, **kwargs) -> List[Dict[str, Any]]:
    return [CoffeeUseFactory().dict() for _ in range(5)]


#### ---- Pytest Fixtures / Hypothesis strategies ---- ####


@pytest.fixture(scope="module")
def mock_bag() -> CoffeeBag:
    return CoffeeBag(brand="FakeCoffee", name="Not real coffee")


@pytest.fixture(scope="module")
def mock_use() -> CoffeeUse:
    return CoffeeUse(bag_id="BAG-ID", datetime=datetime.now())


@st.composite
def coffee_bag_list(draw):
    n = draw(st.integers(0, 20))
    bags = [CoffeeBagFactory() for _ in range(n)]
    for bag in bags:
        if random() < 0.1:
            bag.start = None
    return bags


#### ---- Helper functions ---- ####


def test_today_at_midnight():
    midnight = main.today_at_midnight()
    today = date.today()
    assert midnight.year == today.year
    assert midnight.month == today.month
    assert midnight.day == today.day
    assert midnight.hour == 0
    assert midnight.minute == 0
    assert midnight.second == 0
    assert midnight.microsecond == 0


#### ---- Data modifiers ---- ####


class TestModelDataModifiers:
    @pytest.mark.parametrize(
        "info",
        (
            {},
            {"brand": None, "name": None},
            {"brand": "BRAND"},
            {"brand": None, "name": "NAME"},
        ),
    )
    def test_convert_info_to_bag_fails(self, info: Dict[str, Any]):
        with pytest.raises(Exception):
            _ = main.convert_info_to_bag(info)

    @pytest.mark.parametrize(
        "info",
        (
            {"brand": "BRAND", "name": "NAME"},
            {"brand": "BRAND", "name": "NAME", "key": "KEY"},
            {
                "brand": "BRAND",
                "name": "NAME",
                "weight": 3940832.4980,
                "start": fake.date_object(),
                "finish": fake.date_object(),
            },
            {
                "brand": "BRAND",
                "name": "NAME",
                "weight": 3940832.4980,
                "start": fake.date_object(),
                "finish": fake.date_object(),
                "random_field": "RANDOM_VALUE",
            },
        ),
    )
    def test_convert_info_to_bag_succeeds(self, info: Dict[str, Any]):
        bag = main.convert_info_to_bag(info)
        assert isinstance(bag, CoffeeBag)
        assert bag.brand == info["brand"]
        assert bag.name == info["name"]
        if "key" in info.keys():
            bag._key == info["key"]
        if "weight" in info.keys():
            bag.weight == info["weight"]
        if "start" in info.keys():
            bag.start == info["start"]
        if "finish" in info.keys():
            bag.finish == info["finish"]

    @pytest.mark.parametrize(
        "bag, expected_key",
        (
            [CoffeeBag(brand="BRAND", name="NAME"), None],
            [CoffeeBag(brand="BRAND", name="NAME", key="FAKE-KEY"), "FAKE-KEY"],
        ),
    )
    def test_convert_bag_to_info(self, bag: CoffeeBag, expected_key: Any):
        info = main.convert_bag_to_info(bag)
        assert info["brand"] == bag.brand
        assert info["name"] == bag.name
        assert isinstance(bag._key, str)
        assert info["key"] == bag._key
        if expected_key is not None:
            assert info["key"] == expected_key

    def test_convert_info_to_bag_to_info(self):
        info1: Dict[str, Any] = {
            "brand": fake.company(),
            "name": fake.bs(),
            "key": fake.credit_card_number(),
        }
        bag = main.convert_info_to_bag(info1)
        info2 = main.convert_bag_to_info(bag)
        for key, item in info1.items():
            assert info2[key] == item

    @pytest.mark.parametrize(
        "info",
        (
            {},
            {"bag_id": "BAG_ID"},
            {"bag_id": None},
            {"bag_id": None, "datetime": fake.date_time()},
        ),
    )
    def test_convert_info_to_use_fails(self, info: Dict[str, Any]):
        with pytest.raises(Exception):
            main.convert_info_to_use(info)

    @pytest.mark.parametrize(
        "info",
        (
            {"bag_id": "BAG_ID", "datetime": fake.date_time()},
            {"bag_id": "BAG_ID", "datetime": fake.date_time(), "key": main.make_key()},
        ),
    )
    def test_convert_info_to_use_succeeds(self, info: Dict[str, Any]):
        use = main.convert_info_to_use(info)
        assert isinstance(use, CoffeeUse)
        assert use.bag_id == info["bag_id"]
        assert use.datetime == info["datetime"]
        assert isinstance(use._key, str)
        if "key" in info.keys():
            assert use._key == info["key"]

    def test_convert_use_to_info(self):
        use = CoffeeUse(bag_id="BAG_ID", datetime=datetime.now())
        info = main.convert_use_to_info(use)
        assert info["key"] == use._key
        assert info["datetime"] == jsonable_encoder(use.datetime)
        assert info["bag_id"] == use.bag_id

    def test_convert_info_to_use_info(self):
        info1: Dict[str, Any] = {
            "bag_id": main.make_key(),
            "datetime": jsonable_encoder(fake.date_time()),
        }
        use = main.convert_info_to_use(info1)
        info2 = main.convert_use_to_info(use)
        for key, value in info1.items():
            assert info2[key] == value


#### ---- Database interfacing functions ---- ####


def test_coffee_bag_list(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(main, "get_all_coffee_bag_info", mock_coffee_bag_info)
    bags = main.coffee_bag_list()
    for bag in bags:
        assert isinstance(bag, CoffeeBag)


def test_coffee_bag_dict(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(main, "get_all_coffee_bag_info", mock_coffee_bag_info)
    for key, bag in main.coffee_bag_dict().items():
        assert isinstance(bag, CoffeeBag)
        assert key == bag._key


def test_coffee_use_dict(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(main, "get_all_coffee_use_info", mock_coffee_use_info)
    for key, use in main.coffee_use_dict().items():
        assert isinstance(use, CoffeeUse)
        assert key == use._key


@given(coffee_bag_list())
def test_sort_coffee_bags(bags: List[CoffeeBag]):
    main.sort_coffee_bags(bags)
    if len(bags) < 2:
        assert True
        return

    for i in range(len(bags) - 1):
        a = bags[i - 1]
        b = bags[i]
        if b.start is None:
            assert True
        elif a.start is None:
            assert b.start is None
        else:
            assert a.start <= b.start


#### ---- Base security functions ---- ####

fake_passwords: List[Any] = ["", 1, 100, "a", None, -1, 0.33, math.pi, math.e, sum, any]
fake_passwords += [fake.password() for _ in range(20)]


@pytest.mark.dev
@pytest.mark.parametrize("password", fake_passwords)
def test_compare_password(password: Any):
    assert not main.compare_password(password)  # type: ignore


@pytest.mark.dev
@pytest.mark.parametrize("password", fake_passwords)
def test_verify_password(password: Any):
    with pytest.raises(HTTPException):
        main.verify_password(password)  # type: ignore


#### ---- HTTP Exceptions ---- ####


class TestHttpExceptions:
    def test_raise_bag_not_found(self):
        with pytest.raises(HTTPException) as err:
            main.raise_bag_not_found("not a real bag")
        assert err.value.status_code == 404
        assert "not a real bag" in err.value.detail

    def test_raise_server_error(self):
        with pytest.raises(HTTPException) as err:
            main.raise_server_error(Exception("some exception"))
        assert err.value.status_code == 500
        assert "some exception" in err.value.detail

    def test_raise_invalid_field(self):
        with pytest.raises(HTTPException) as err:
            main.raise_invalid_field("SOME FIELD")
        assert err.value.status_code == 404
        assert "SOME FIELD" in str(err.value.detail)


#### ---- Getters ---- ####


def test_get_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Coffee Counter API"}


@pytest.mark.parametrize(
    "endpoint",
    (
        "/",
        "/docs/",
        "/bags/",
        "/number_of_bags/",
        "/active_bags/",
        "/uses/",
        "/number_of_uses/",
    ),
)
def test_real_getter_endpoints(endpoint: str):
    response = client.get(endpoint)
    assert response.status_code == 200
