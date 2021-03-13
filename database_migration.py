#!/usr/bin/env python3

import main


def introduce_active_attribute():
    num_bags = 0
    for bag in main.coffee_bag_list():
        num_bags += 1
        info = main.convert_bag_to_info(bag)
        main.coffee_bag_db.put(info)
    print(f"Converted {num_bags} bags.")


def migrate():
    # introduce_active_attribute()
    print("Done")


if __name__ == "__main__":
    migrate()
