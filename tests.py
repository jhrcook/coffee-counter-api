#!/usr/bun/env python3

from datetime import datetime
from random import choices, randint
from string import printable
from uuid import uuid1

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from main import CoffeeBag, CoffeeUse, app, get_uses, today_at_midnight

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


#### ---- Data modifiers ---- ####

# convert_info_to_bag
# convert_bag_to_info
# convert_info_to_use
# convert_use_to_info
# keyedlist_to_dict

#### ---- Data base interfacing functions ---- ####

# get_all_detabase_info
# get_all_coffee_bag_info
# coffee_bag_list
# coffee_bag_dict
# get_all_coffee_use_info
# coffee_use_dict
# sort_coffee_bags


#### ---- Meta Database ---- ####

# num_coffee_bags
# num_coffee_uses

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
