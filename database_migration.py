#!/usr/bin/env python3

from main import coffee_bag_db, coffee_bag_list, convert_bag_to_info


def introduce_active_attribute():
    num_bags = 0
    for bag in coffee_bag_list():
        num_bags += 1
        info = convert_bag_to_info(bag)
        coffee_bag_db.put(info)
    print(f"Converted {num_bags} bags.")


if __name__ == "__main__":
    introduce_active_attribute()
