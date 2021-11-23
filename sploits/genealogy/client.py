from typing import Optional

import httpx


class GenealogyClient:
    def __init__(self, url):
        self.client = httpx.Client(base_url=url)

    def __enter__(self) -> "GenealogyClient":
        self.client.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.__exit__(exc_type, exc_val, exc_tb)

    def create_user(self, login: str, password: str) -> int:
        r = self.client.post("/users", json={"login": login, "password": password})
        r.raise_for_status()
        response = r.json()
        print(f"[+] Registered user {login} with id = {response['user']['id']}")
        return response["user"]["id"]

    def login(self, login: str, password: str):
        r = self.client.post("/login", json={"login": login, "password": password})
        r.raise_for_status()

    def create_tree(self, title: str, description: str, person_id: Optional[int] = None) -> int:
        r = self.client.post("/tree", json={"title": title, "description": description, "person": person_id})
        r.raise_for_status()
        return r.json()["tree"]["id"]

    def update_tree(self, description: str, person_id: int):
        r = self.client.put("/tree", json={"description": description, "person": person_id})
        r.raise_for_status()

    def get_tree(self) -> dict:
        r = self.client.get("/tree")
        r.raise_for_status()
        return r.json()["tree"]

    def create_person(
        self, name: str, birth_date: int, death_date: int,
        first_parent_id: Optional[int], second_parent_id: Optional[int],
    ) -> int:
        r = self.client.post("/tree/persons", json={
            "title": "",
            "first_name": name,
            "middle_name": "",
            "last_name": "",
            "photo_url": "",
            "birth_date": birth_date,
            "death_date": death_date,
            "first_parent": first_parent_id,
            "second_parent": second_parent_id,
        })
        r.raise_for_status()
        return r.json()["person"]["id"]

    def update_person(
        self, person_id: int, name: str, birth_date: int, death_date: int,
        first_parent_id: Optional[int], second_parent_id: Optional[int],
    ):
        r = self.client.put(f"/tree/persons/{person_id}", json={
            "name": name,
            "birth_date": birth_date,
            "death_date": death_date,
            "first_parent": first_parent_id,
            "second_parent": second_parent_id,
        })
        r.raise_for_status()

    def delete_person(self, person_id):
        r = self.client.delete(f"/tree/persons/{person_id}")
        r.raise_for_status()

    def update_owners(self, owners: list[int]):
        r = self.client.put(f"/tree/owners", json=owners)
        r.raise_for_status()

    def download_tree_archive(self) -> bytes:
        r = self.client.get("/tree/archive")
        return r.content

    def check_tree_archive(self, archive: bytes) -> dict:
        r = self.client.post("/tree/archive", content=archive)
        r.raise_for_status()
        print(r.content)
        return r.json()