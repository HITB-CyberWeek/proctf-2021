#!/usr/bin/env python3
import json
import logging
import random
import string
from typing import Optional

import checklib.http
import checklib.random


class GenealogyChecker(checklib.http.HttpJsonChecker):
    port = 8888
    proto = 'http'

    def info(self):
        print("vulns: 1")
        print("public_flag_description: Flag ID is just a user's ID, flag is a genealogy tree's title")

    def check(self, address):
        login = checklib.random.firstname().lower() + "_" + checklib.random.lastname().lower()
        password = checklib.random.string(string.ascii_letters + string.digits, random.randint(8, 12))
        self.create_user(login, password)

        grandparent1 = self.generate_random_person(None, None)
        parent1 = self.generate_random_person(grandparent1, None)
        parent2 = self.generate_random_person(None, None)
        person_id = self.generate_random_person(parent1, parent2)

        tree_title = "My genealogy tree"
        tree_description = f"The genealogy tree of @{login}"
        self.create_tree(tree_title, tree_description, person_id)

        tree = self.get_tree()

        self.corrupt_if_false("person" in tree, "Invalid tree on GET /tree", "No person key in the tree")
        self.corrupt_if_false("parents" in tree["person"], "Invalid tree on GET /tree", "No person.parents key in the tree")
        self.corrupt_if_false(len(tree["person"]["parents"]) == 2, "Invalid tree on GET /tree", "The length of person.parents field is not equal to 2")

        parent = tree["person"]["parents"][0]
        if parent["id"] != parent1:
            parent = tree["person"]["parents"][0]
        self.corrupt_if_false(parent["id"] == parent1, "Invalid tree on GET /tree", f"Invalid value of person.parents[].id, should be {parent}")
        self.corrupt_if_false(len(parent["parents"]) == 1, "Invalid tree on GET /tree", "The length of person.parents.parents field is not equal to 1")
        self.corrupt_if_false(parent["parents"][0]["id"] == grandparent1, "Invalid tree on GET /tree", f"Invalid value of person.parents[].parents[].id, should be {grandparent1}")

        self.exit(checklib.StatusCode.OK)

    def put(self, address, flag_id, flag, vuln):
        login = checklib.random.firstname().lower() + "_" + checklib.random.lastname().lower()
        password = checklib.random.string(string.ascii_letters + string.digits, random.randint(8, 12))
        user_id = self.create_user(login, password)

        title = random.choice(["Mr", "Mrs"])
        first_name = checklib.random.firstname()
        middle_name = checklib.random.firstname()
        last_name = checklib.random.lastname()
        photo_url = f"https://gravatar.com/{first_name}_{last_name}"
        birth_date = random.randint(974801564, 1290334364)
        death_date = birth_date + random.randint(30, 100) * 365 * 24 * 60 * 60
        person_id = self.create_person(title, first_name, middle_name, last_name, photo_url, birth_date, death_date, None, None)

        tree_title = flag
        tree_description = checklib.random.string(string.ascii_letters + " ", random.randint(10, 100))
        self.create_tree(tree_title, tree_description, person_id)

        owners = list(random.sample(list(range(10000)), random.randint(1, 10)))
        self.update_owners(owners)

        print(json.dumps({
            "public_flag_id": user_id,
            "login": login,
            "password": password,
            "tree": {
                "title": tree_title,
                "description": tree_description,
                "owners": owners,
                "person": {
                    "title": title,
                    "first_name": first_name,
                    "middle_name": middle_name,
                    "last_name": last_name,
                    "photo_url": photo_url,
                    "birth_date": birth_date,
                }
            }
        }))

        self.exit(checklib.StatusCode.OK)

    def get(self, address, flag_id, flag, vuln):
        info = json.loads(flag_id)
        self.login(info["login"], info["password"])

        tree = info["tree"]

        archive = self.download_tree_archive()
        downloaded_tree = self.check_tree_archive(archive)
        if "tree" not in downloaded_tree:
            self.exit(checklib.StatusCode.MUMBLE, "Invalid response on GET /tree: no 'tree' key")
        downloaded_tree = downloaded_tree["tree"]

        self.mumble_if_false("title" in downloaded_tree, "Invalid response on GET /tree: no 'title' key")
        self.mumble_if_false("description" in downloaded_tree, "Invalid response on GET /tree: no 'description' key")

        self.corrupt_if_false(
            downloaded_tree["title"] == tree["title"],
            "Could not find flag in the genealogy tree for user " + info["login"]
        )
        self.corrupt_if_false(
            downloaded_tree["description"] == tree["description"],
            "Genealogy tree for user " + info["login"] + " corrupted: description mismatch"
        )

        for person_field, person_field_value in tree["person"].items():
            self.mumble_if_false(person_field in downloaded_tree["person"], f"Invalid response on GET /tree: no {person_field} key")
            self.corrupt_if_false(
                downloaded_tree["person"][person_field] == person_field_value,
                f"Genealogy tree for user {info['login']} corrupted: person.{person_field} mismatch"
            )

        self.corrupt_if_false(
            set(downloaded_tree["owners"]) == set(tree["owners"]),
            f"Genealogy tree for user {info['login']} corrupted: owners mismatch"
        )

        self.exit(checklib.StatusCode.OK)

    # Internal methods below

    def generate_random_person(self, first_parent_id: Optional[int], second_parent_id: Optional[int]):
        title = random.choice(["Mr", "Mrs"])
        first_name = checklib.random.firstname()
        middle_name = checklib.random.firstname()
        last_name = checklib.random.lastname()
        photo_url = f"https://gravatar.com/{first_name}_{last_name}"
        birth_date = random.randint(974801564, 1290334364)
        death_date = birth_date + random.randint(30, 100) * 365 * 24 * 60 * 60
        person_id = self.create_person(
            title, first_name, middle_name, last_name, photo_url, birth_date, death_date,
            first_parent_id, second_parent_id
        )
        return person_id

    def create_user(self, login: str, password: str) -> int:
        logging.info(f"Creating user {login} with password {password}")
        r = self.try_http_post("/users", json={"login": login, "password": password})
        self.mumble_if_false("user" in r and "id" in r["user"], "Invalid format of response on POST /users")

        user_id = r["user"]["id"]
        logging.info(f"Created user with id {user_id}")
        return user_id

    def login(self, login: str, password: str):
        logging.info(f"Authenticating as {login} with password {password}")
        self.try_http_post("/login", json={"login": login, "password": password})

    def create_tree(self, title: str, description: str, person_id: Optional[int] = None) -> int:
        logging.info(f"Creating tree {title!r} with description {description!r}")
        r = self.try_http_post("/tree", json={"title": title, "description": description, "person": person_id})
        self.mumble_if_false("tree" in r and "id" in r["tree"], "Invalid format of response on POST /tree")
        return r["tree"]["id"]

    def update_tree(self, description: str, person_id: int):
        logging.info(f"Updating tree: set description {description!r} and person {person_id}")
        self.try_http_put("/tree", json={"description": description, "person": person_id})

    def get_tree(self) -> dict:
        r = self.try_http_get("/tree")
        self.mumble_if_false("tree" in r, "Invalid format of response on GET /tree")
        return r["tree"]

    def create_person(
        self, title: str, first_name: str, middle_name: str, last_name: str, photo_url: str,
        birth_date: int, death_date: int,
        first_parent_id: Optional[int], second_parent_id: Optional[int],
    ) -> int:
        logging.info(f"Creating person {title} {first_name} {middle_name} {last_name}: {birth_date} - {death_date}, "
                     f"parents: {first_parent_id}, {second_parent_id}")
        r = self.try_http_post("/tree/persons", json={
            "title": title,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "photo_url": photo_url,
            "birth_date": birth_date,
            "death_date": death_date,
            "first_parent": first_parent_id,
            "second_parent": second_parent_id,
        })
        return r["person"]["id"]

    def update_person(
        self, person_id: int, title: str, first_name: str, middle_name: str, last_name: str, photo_url: str,
        birth_date: int, death_date: int, first_parent_id: Optional[int], second_parent_id: Optional[int],
    ):
        logging.info(f"Updating person {person_id}: {title} {first_name} {middle_name} {last_name}: {birth_date} - {death_date}, "
                     f"parents: {first_parent_id}, {second_parent_id}")
        self.try_http_put(f"/tree/persons/{person_id}", json={
            "title": title,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "photo_url": photo_url,
            "birth_date": birth_date,
            "death_date": death_date,
            "first_parent": first_parent_id,
            "second_parent": second_parent_id,
        })

    def delete_person(self, person_id):
        logging.info(f"Deleting person {person_id}")
        self.try_http_delete(f"/tree/persons/{person_id}")

    def update_owners(self, owners: list[int]):
        logging.info(f"Updating tree's owners: {owners!r}")
        self.try_http_put(f"/tree/owners", json=owners)

    def download_tree_archive(self) -> bytes:
        logging.info(f"Downloading signed tree archive")
        r = self.try_http_get("/tree/archive", no_json=True)
        return r.content

    def check_tree_archive(self, archive: bytes) -> dict:
        logging.info(f"Checking tree archive")
        return self.try_http_post("/tree/archive", data=archive)


if __name__ == "__main__":
    GenealogyChecker().run()
