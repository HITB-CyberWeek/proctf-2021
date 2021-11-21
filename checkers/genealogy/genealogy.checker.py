#!/usr/bin/env python3
import json
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
        print("public_flag_description: Flag id is just a user id")

    def check(self, address):
        self.exit(checklib.StatusCode.OK)

    def put(self, address, flag_id, flag, vuln):
        login = checklib.random.firstname().lower() + "_" + checklib.random.lastname().lower()
        password = checklib.random.string(string.ascii_letters + string.digits, random.randint(8, 12))
        user_id = self.create_user(login, password)

        name = checklib.random.firstname() + " " + checklib.random.lastname()
        birth_date = random.randint(1000, 10000000)
        death_date = birth_date + random.randint(30, 100) * 365 * 24 * 60 * 60
        person_id = self.create_person(name, birth_date, death_date, None, None)

        tree_title = flag
        tree_description = checklib.random.string(string.ascii_letters + " ", random.randint(10, 100))
        self.create_tree(tree_title, tree_description, person_id)

        # TODO: check /owners url

        print(json.dumps({
            "public_flag_id": user_id,
            "login": login,
            "password": password,
            "tree": {
                "title": tree_title,
                "description": tree_description,
                "person": {
                    "name": name,
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

        if "title" not in downloaded_tree:
            self.exit(checklib.StatusCode.MUMBLE, "Invalid response on GET /tree: no 'title' key")
        if "description" not in downloaded_tree:
            self.exit(checklib.StatusCode.MUMBLE, "Invalid response on GET /tree: no 'description' key")

        if downloaded_tree["title"] != tree["title"]:
            self.exit(checklib.StatusCode.CORRUPT, "Could not find flag in the genealogy tree for user " + info["login"])

        if downloaded_tree["description"] != tree["description"]:
            self.exit(checklib.StatusCode.CORRUPT, "Genealogy tree for user " + info["login"] + " corrupted: description mismatch")

        # TODO check other fields

        self.exit(checklib.StatusCode.OK)

    def create_user(self, login: str, password: str) -> int:
        r = self.try_http_post("/users", json={"login": login, "password": password})
        self.mumble_if_false("user" in r and "id" in r["user"], "Invalid format of response on POST /users")
        return r["user"]["id"]

    def login(self, login: str, password: str):
        self.try_http_post("/login", json={"login": login, "password": password})

    def create_tree(self, title: str, description: str, person_id: Optional[int] = None) -> int:
        r = self.try_http_post("/tree", json={"title": title, "description": description, "person": person_id})
        self.mumble_if_false("tree" in r and "id" in r["tree"], "Invalid format of response on POST /tree")
        return r["tree"]["id"]

    def update_tree(self, title: str, description: str, person_id: int):
        self.try_http_put("/tree", json={"title": title, "description": description, "person": person_id})

    def get_tree(self) -> dict:
        r = self.try_http_get("/tree")
        self.mumble_if_false("tree" in r, "Invalid format of response on GET /tree")
        return r["tree"]

    def create_person(
        self, name: str, birth_date: int, death_date: int,
        first_parent_id: Optional[int], second_parent_id: Optional[int],
    ) -> int:
        r = self.try_http_post("/tree/persons", json={
            "title": "Mr",
            "first_name": name,
            # TODO ↓
            "middle_name": "",
            "last_name": "",
            "photo_url": "",
            # TODO ↑
            "birth_date": birth_date,
            "death_date": death_date,
            "first_parent": first_parent_id,
            "second_parent": second_parent_id,
        })
        return r["person"]["id"]

    def update_person(
        self, person_id: int, name: str, birth_date: int, death_date: int,
        first_parent_id: Optional[int], second_parent_id: Optional[int],
    ):
        self.try_http_put(f"/tree/persons/{person_id}", json={
            "name": name,
            "birth_date": birth_date,
            "death_date": death_date,
            "first_parent": first_parent_id,
            "second_parent": second_parent_id,
        })

    def delete_person(self, person_id):
        self.try_http_delete(f"/tree/persons/{person_id}")

    def update_owners(self, owners: list[int]):
        self.try_http_put(f"/tree/owners", json=owners)

    def download_tree_archive(self) -> bytes:
        r = self.try_http_get("/tree/archive", no_json=True)
        return r.content

    def check_tree_archive(self, archive: bytes) -> dict:
        return self.try_http_post("/tree/archive", data=archive)


if __name__ == "__main__":
    GenealogyChecker().run()
