from typing import Optional

import httpx


class GenealogyClient:
    def __init__(self, url):
        self.client = httpx.AsyncClient(base_url=url)

    async def __aenter__(self) -> "GenealogyClient":
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def create_user(self, login: str, password: str) -> int:
        r = await self.client.post("/users", json={"login": login, "password": password})
        r.raise_for_status()
        response = r.json()
        print(f"[+] Registered user {login} with id = {response['user']['id']}")
        return response["user"]["id"]

    async def login(self, login: str, password: str):
        r = await self.client.post("/login", json={"login": login, "password": password})
        r.raise_for_status()

    async def create_tree(self, title: str, description: str, person_id: Optional[int] = None) -> int:
        r = await self.client.post("/tree", json={"title": title, "description": description, "person": person_id})
        r.raise_for_status()
        return r.json()["tree"]["id"]

    async def update_tree(self, title: str, description: str, person_id: int):
        r = await self.client.put("/tree", json={"title": title, "description": description, "person": person_id})
        r.raise_for_status()

    async def get_tree(self) -> dict:
        r = await self.client.get("/tree")
        r.raise_for_status()
        return r.json()["tree"]

    async def create_person(
        self, name: str, birth_date: int, death_date: int,
        first_parent_id: Optional[int], second_parent_id: Optional[int],
    ) -> int:
        r = await self.client.post("/tree/persons", json={
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

    async def update_person(
        self, person_id: int, name: str, birth_date: int, death_date: int,
        first_parent_id: Optional[int], second_parent_id: Optional[int],
    ):
        r = await self.client.put(f"/tree/persons/{person_id}", json={
            "name": name,
            "birth_date": birth_date,
            "death_date": death_date,
            "first_parent": first_parent_id,
            "second_parent": second_parent_id,
        })
        r.raise_for_status()

    async def delete_person(self, person_id):
        r = await self.client.delete(f"/tree/persons/{person_id}")
        r.raise_for_status()

    async def update_owners(self, owners: list[int]):
        r = await self.client.put(f"/tree/owners", json=owners)
        r.raise_for_status()

    async def download_tree_archive(self) -> bytes:
        r = await self.client.get("/tree/archive")
        return r.content

    async def check_tree_archive(self, archive: bytes) -> dict:
        r = await self.client.post("/tree/archive", content=archive)
        r.raise_for_status()
        print(r.content)
        return r.json()