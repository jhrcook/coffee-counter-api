#!/usr/bin/env python3

# A script to instantiate the meta tracking data base with the
# current values. This script needs only be run once as a
# simple database migration.
#
# last run 3/11/2021 by JHC
#

from main import META_DB_KEY as DB_KEY
from main import MetaDataField, coffee_bag_db, coffee_use_db, meta_db


def instantiate_meta_database():

    num_coffee_bags, num_coffee_uses = 0, 0

    for page in coffee_bag_db.fetch(query=None, buffer=500, pages=100):
        num_coffee_bags += len(page)

    print(f"Number of coffee bags: {num_coffee_bags}")

    for page in coffee_use_db.fetch(query=None, buffer=500, pages=100):
        num_coffee_uses += len(page)

    print(f"Number of coffee uses: {num_coffee_uses}")

    meta_db.put(
        {
            MetaDataField.bag_count: num_coffee_bags,
            MetaDataField.use_count: num_coffee_uses,
        },
        key=DB_KEY,
    )
    return None


if __name__ == "__main__":
    instantiate_meta_database()
    print("Done")
