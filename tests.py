"""Test the coffee counting API."""

from datetime import date, datetime, timedelta
from random import choices, randint, random
from string import printable
from typing import Any, Dict, List

import factory
import pytest
from faker import Faker
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

import main
from main import CoffeeBag, CoffeeUse, app, today_at_midnight

main.PROJECT_KEY = ""

client = TestClient(app)

fake = Faker()
fake.seed_instance(123)


@pytest.fixture(scope="module")
def mock_bag() -> CoffeeBag:
    return CoffeeBag(brand="FakeCoffee", name="Not real coffee")


@pytest.fixture(scope="module")
def mock_use() -> CoffeeUse:
    return CoffeeUse(bag_id="BAG-ID", datetime=datetime.now())


def mock_password() -> str:
    k = randint(10, 50)
    return "".join(choices(list(printable), k=k))


def gen_datetime(min_year: int = 1900, max_year: int = datetime.now().year) -> datetime:
    # generate a datetime in format yyyy-mm-dd hh:mm:ss.000000
    start = datetime(min_year, 1, 1, 00, 00, 00)
    years = max_year - min_year + 1
    end = start + timedelta(days=365 * years)
    return start + (end - start) * random()


def gen_date(min_year: int = 1900, max_year: int = datetime.now().year) -> date:
    return gen_datetime(min_year, max_year).date()


def gen_datetime_fmt(min_year: int = 1900, max_year: int = datetime.now().year) -> str:
    return gen_datetime(min_year, max_year).strftime("%Y-%m-%dT%H:%M:%S")


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
                "start": gen_date(),
                "finish": gen_date(),
            },
            {
                "brand": "BRAND",
                "name": "NAME",
                "weight": 3940832.4980,
                "start": gen_date(),
                "finish": gen_date(),
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
            "brand": mock_password(),
            "name": mock_password(),
            "key": mock_password(),
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
            {"bag_id": None, "datetime": gen_datetime()},
        ),
    )
    def test_convert_info_to_use_fails(self, info: Dict[str, Any]):
        with pytest.raises(Exception):
            main.convert_info_to_use(info)

    @pytest.mark.parametrize(
        "info",
        (
            {"bag_id": "BAG_ID", "datetime": gen_datetime()},
            {"bag_id": "BAG_ID", "datetime": gen_datetime(), "key": mock_password()},
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
            "bag_id": mock_password(),
            "datetime": jsonable_encoder(gen_datetime()),
        }
        use = main.convert_info_to_use(info1)
        info2 = main.convert_use_to_info(use)
        for key, value in info1.items():
            assert info2[key] == value


#### ---- Database interfacing functions ---- ####


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


@st.composite
def coffee_bag_list(draw):
    n = draw(st.integers(0, 20))
    bags = [CoffeeBagFactory() for _ in range(n)]
    return bags


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
