#!/usr/bun/env python3

from datetime import date, datetime, timedelta
from random import choices, randint, random
from string import printable
from typing import Any, Dict
from uuid import uuid1

import pytest
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

import main
from main import CoffeeBag, CoffeeUse, app, today_at_midnight

client = TestClient(app)


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
    return gen_datetime().date()


def gen_datetime_fmt(min_year: int = 1900, max_year: int = datetime.now().year) -> str:
    return gen_datetime(min_year, max_year).strftime("%Y-%m-%dT%H:%M:%S")


#### ---- Data modifiers ---- ####


class TestModelDataModifiers:
    def test_convert_info_to_bag(self):
        info: Dict[str, Any] = {}
        with pytest.raises(Exception):
            _ = main.convert_info_to_bag(info)

        info["brand"] = None
        info["name"] = None
        with pytest.raises(Exception):
            _ = main.convert_info_to_bag(info)

        info["brand"] = "BRAND"
        with pytest.raises(Exception):
            _ = main.convert_info_to_bag(info)

        info["brand"] = None
        info["name"] = "NAME"
        with pytest.raises(Exception):
            _ = main.convert_info_to_bag(info)

        info["brand"] = "BRAND"
        info["name"] = "NAME"
        bag = main.convert_info_to_bag(info)
        assert isinstance(bag, CoffeeBag)
        assert bag.brand == "BRAND"
        assert bag.name == "NAME"

        info["key"] = "KEY"
        bag = main.convert_info_to_bag(info)
        assert bag._key == info["key"]

        info["weight"] = 3940832.4980
        info["start"] = gen_date()
        info["finish"] = gen_date()
        bag = main.convert_info_to_bag(info)
        assert bag._key == info["key"]
        assert bag.weight == info["weight"]
        assert bag.start == info["start"]
        assert bag.finish == info["finish"]

        info["random_field"] = "RANDOM_VALUE"
        bag = main.convert_info_to_bag(info)
        assert isinstance(bag, CoffeeBag)

    def test_convert_bag_to_info(self):
        bag = CoffeeBag(brand="BRAND", name="NAME")
        info = main.convert_bag_to_info(bag)
        assert info["brand"] == bag.brand
        assert info["name"] == bag.name
        assert isinstance(bag._key, str)

        info["key"] = "FAKE-KEY"
        info = main.convert_bag_to_info(bag)
        assert info["key"] == bag._key

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

    def test_convert_info_to_use(self):
        info: Dict[str, Any] = {}
        with pytest.raises(Exception):
            main.convert_info_to_use(info)

        info["bag_id"] = "BAG_ID"
        with pytest.raises(Exception):
            main.convert_info_to_use(info)

        info["bag_id"] = None
        info["datetime"] = gen_datetime()
        with pytest.raises(Exception):
            main.convert_info_to_use(info)

        info["bag_id"] = "BAG_ID"
        use = main.convert_info_to_use(info)
        assert use.bag_id == info["bag_id"]
        assert use.datetime == info["datetime"]
        assert isinstance(use._key, str)

        info["key"] = mock_password()
        use = main.convert_info_to_use(info)
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


#### ---- Data base interfacing functions ---- ####

# get_all_detabase_info
# get_all_coffee_bag_info
# coffee_bag_list
# coffee_bag_dict
# get_all_coffee_use_info
# coffee_use_dict
# sort_coffee_bags


#### ---- Meta Database ---- ####


@pytest.mark.getter
class TestMetaDatabase:
    def test_num_coffee_bags(self):
        n_bags = main.num_coffee_bags()
        assert isinstance(n_bags, int)
        assert n_bags > 0

    def test_num_coffee_uses(self):
        n_uses = main.num_coffee_uses()
        assert isinstance(n_uses, int)
        assert n_uses > 0


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
        assert "SOME FIELD" in err.value.detail


#### ---- Test Getters ---- ####
@pytest.mark.getter
class TestGetters:
    @pytest.fixture
    def bag_id(self) -> str:
        return "66383fb3-832f-4f1c-987a-f7e410ab5f71"

    def test_read_root(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_get_bags(self):
        response = client.get("/bags/")
        assert response.status_code == 200
        bag_info = response.json()
        for key, info in bag_info.items():
            assert isinstance(key, str)
            bag = CoffeeBag(_key=key, **info)
            assert isinstance(bag, CoffeeBag)

    def test_get_number_of_bags(self):
        response = client.get("/number_of_bags/")
        assert response.status_code == 200
        assert isinstance(response.json(), int)
        assert response.json() > 0

    def test_get_bag_info(self, bag_id: str):
        response = client.get(f"/bag/{bag_id}")
        assert response.status_code == 200

    def test_get_bag_info_fake_bag(self, mock_bag: CoffeeBag):
        response = client.get(f"/bag/{mock_bag._key}")
        assert response.status_code == 404

    def test_get_active_bags(self):
        response = client.get("/active_bags/")
        assert response.status_code == 200
        for key, info in response.json().items():
            assert isinstance(CoffeeBag(_key=key, **info), CoffeeBag)

    def test_get_active_bags_n_last(self):
        response = client.get("/active_bags/?n_last=1")
        assert response.status_code == 200
        assert len(response.json().keys()) <= 1

        response = client.get("/active_bags/?n_last=0")
        assert response.status_code != 200

    def test_get_uses_defaults(self):
        response = client.get("/uses/")
        assert response.status_code == 200
        assert len(response.json().keys()) > 0
        for key, info in response.json().items():
            assert isinstance(CoffeeUse(_key=key, **info), CoffeeUse)

    def test_get_uses_n_last(self):
        response = client.get("/uses/?n_last=5")
        assert response.status_code == 200
        assert len(response.json().keys()) == 5
        for key, info in response.json().items():
            assert isinstance(CoffeeUse(_key=key, **info), CoffeeUse)

        response = client.get("/uses/?n_last=1")
        assert response.status_code == 200
        assert len(response.json().keys()) == 1
        for key, info in response.json().items():
            assert isinstance(CoffeeUse(_key=key, **info), CoffeeUse)

        response = client.get("/uses/?n_last=0")
        assert response.status_code != 200

    def test_get_uses_since(self):
        _date = today_at_midnight().strftime("%Y-%m-%dT%H:%M:%S")
        dates = [_date, _date + ".00"]  # try multiple date formats
        for date in dates:
            response = client.get(f"/uses/?since={date}")
            assert response.status_code == 200
            assert len(response.json().keys()) >= 0
            for key, info in response.json().items():
                assert isinstance(CoffeeUse(_key=key, **info), CoffeeUse)

    def test_get_uses_bag_id(self, bag_id: str):
        response = client.get(f"/uses/?bag_id={bag_id}")
        assert response.status_code == 200
        assert len(response.json().keys()) >= 0
        for key, info in response.json().items():
            assert isinstance(CoffeeUse(_key=key, **info), CoffeeUse)

    def test_get_uses_fake_bag_id(self):
        response = client.get(f"/uses/?bag_id={mock_password()}")
        assert response.status_code == 200
        assert len(response.json().keys()) == 0

    def test_get_number_of_uses(self):
        response = client.get("/number_of_uses/")
        assert response.status_code == 200
        assert isinstance(response.json(), int)

    def test_get_number_of_uses_since(self):
        for _ in range(N_TRIES):
            response = client.get(f"/number_of_uses/?since={gen_datetime_fmt()}")
            assert response.status_code == 200
            assert isinstance(response.json(), int)

    def test_get_number_of_uses_bag_id(self, bag_id: str):
        response = client.get(f"/number_of_uses/?bag_id={bag_id}")
        assert response.status_code == 200
        assert isinstance(response.json(), int)
        assert response.json() > 0

    def test_get_number_of_uses_since_bag_id(self, bag_id: str):
        for _ in range(N_TRIES):
            response = client.get(
                f"/number_of_uses/?since={gen_datetime_fmt()}&bag_id={bag_id}"
            )
            assert response.status_code == 200
            assert isinstance(response.json(), int)


#### ---- Test Passwords ---- ####

N_TRIES = 5


@pytest.mark.setter
class TestSetterPasswords:
    def test_add_new_bag_password(self, mock_bag: CoffeeBag):
        for _ in range(N_TRIES):
            response = client.put(
                f"/new_bag/?password={mock_password()}", json=jsonable_encoder(mock_bag)
            )
            assert response.status_code == 401
        response = client.put("/new_bag/?password=", json=jsonable_encoder(mock_bag))
        assert response.status_code == 401

    def test_add_new_use_password(self, mock_bag: CoffeeBag):
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

    def test_deactivate_bag_password(self, mock_bag: CoffeeBag):
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

    def test_activate_bag_password(self, mock_bag: CoffeeBag):
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

    def test_update_bag_password(self, mock_bag: CoffeeBag):
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

    def test_delete_bag_password(self, mock_bag: CoffeeBag):
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

    def test_delete_bags_password(self):
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

    # NOTE: Careful not to use random passwords for this test
    def test_delete_all_bags_password(self):
        response = client.delete("/delete_all_bags/?password=")
        assert response.status_code == 401
        response = client.delete("/delete_all_bags/?password=not-the-password")
        assert response.status_code == 401

    def test_delete_use_password(self, mock_use: CoffeeUse):
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

    def test_delete_uses_password(self):
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

    # NOTE: Careful not to use random passwords for this test
    def test_delete_all_uses_password(self):
        response = client.delete("/delete_all_uses/?password=")
        assert response.status_code == 401
        response = client.delete("/delete_all_uses/?password=not-the-password")
        assert response.status_code == 401
