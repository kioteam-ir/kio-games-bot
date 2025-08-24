from typing import List
from orm import SponserModel

class SponsorType:

    def __init__(self, sponsor_id: int, name: str, link: str):
        self.id = sponsor_id
        self.name = name
        self.link = link

    def __repr__(self):
        return f"SponsorType(id={self.id}, name='{self.name}', link='{self.link}')"


class SponsorCache:

    def __init__(self):
        self._cache: List[SponsorType] = []
        self.update_all()

    def get_all(self) -> List[SponsorType]:
        if not self._cache:
            self.update_all()
        return self._cache

    def update_all(self) -> None:
        self._cache = [
            SponsorType(
                sponsor_id=row["id"],
                name=row["name"],
                link=row["link"]
            )
            for row in  SponserModel.get_all()
        ]
sponsor_cache = SponsorCache()