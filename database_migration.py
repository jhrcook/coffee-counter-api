#!/usr/bin/env python3

import main


def introduce_active_attribute_to_coffee_bags():
    num_bags = 0
    for bag in main.coffee_bag_list():
        num_bags += 1
        info = main.convert_bag_to_info(bag)
        main.coffee_bag_db.put(info)
    print(f"Converted {num_bags} bags.")


def add_seconds_attribute_to_coffee_uses():
    coffee_uses = main.coffee_use_dict()
    n = 0
    for key, coffee_use in coffee_uses.items():
        try:
            main.coffee_use_db.update({"_seconds": coffee_use._seconds}, key=key)
            n += 1
        except Exception as err:
            print(f"Error: {err}")
            print("CoffeeUse:")
            print(coffee_use.dict())
            return
    print(f"Converted {n} uses.")


def migrate():
    # introduce_active_attribute_to_coffee_bags()
    # add_seconds_attribute_to_coffee_uses()
    print("Done")


if __name__ == "__main__":
    migrate()
