# ruff: noqa: E501
from bot.domain.schemas.game import GameCatalogEntry, GameTypeId

GAME_CATALOG: dict[str, dict[GameTypeId, GameCatalogEntry]] = {
    "fa": {
        GameTypeId.XO: GameCatalogEntry(
            title="XO GAME | بازی دایره و ضرب",
            id=GameTypeId.XO,
            description="❌⭕️ بازی ضرب در و خانه معروف به دوز ❌⭕️",
            thumb_url="https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Tic_tac_toe.svg/1200px-Tic_tac_toe.svg.png",
            rows=3,
            cols=3,
            connect=3,
        ),
        GameTypeId.CONNECT_3: GameCatalogEntry(
            title="CONNECT 3 | 3 تاشو وصل کن !",
            id=GameTypeId.CONNECT_3,
            description="🥇 فقط کافیه که 3 تا از مهره هاتو پشت سرهم بچینی. یا افقی یا عمودی و یا ضرب‌دری 🥇",
            thumb_url="https://lh6.googleusercontent.com/proxy/TYpZrjlqu_tnJvoNtKQHNZXwlxuCbZxEsO_Aq09iS5KAcUDKPaU9mHlr6pLl5Nvyk28rd6y_JoL4aqrxZ0tRQgSKT0ewVMAybrqk20W-UznJCA22AfUyVyTcHm2rRnh18Fa3K5PIXYgSaVs",
            rows=6,
            cols=7,
            connect=3,
        ),
        GameTypeId.CONNECT_4: GameCatalogEntry(
            title="CONNECT 4 | 4 تاشو وصل کن !",
            id=GameTypeId.CONNECT_4,
            description="🥇 فقط کافیه که 4 تا از مهره هاتو پشت سرهم بچینی. یا افقی یا عمودی و یا ضرب‌دری 🥇",
            thumb_url="https://www.researchgate.net/profile/Gaetan-Sanchez/publication/258381798/figure/fig1/AS:311148797808643@1451195062476/Traditional-Connect-Four-Here-Red-wins-with-four-coins-aligned-diagonally.png",
            rows=6,
            cols=7,
            connect=4,
        ),
        GameTypeId.CONNECT_5: GameCatalogEntry(
            title="CONNECT 5 | 5 تاشو وصل کن !",
            id=GameTypeId.CONNECT_5,
            description="🥇 فقط کافیه که 5 تا از مهره هاتو پشت سرهم بچینی. یا افقی یا عمودی و یا ضرب‌دری 🥇",
            thumb_url="https://static.drimify.com/wp-content/uploads/2024/12/screenshot-415-min.png",
            rows=8,
            cols=8,
            connect=5,
        ),
        GameTypeId.MINE: GameCatalogEntry(
            title="MINEROB | مین‌روب",
            id=GameTypeId.MINE,
            description="💣 بازی مین‌روب نوبتی دو نفره — خانه‌ها را باز کن و امتیاز جمع کن! 💣",
            thumb_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Minesweeper_64x64.png/240px-Minesweeper_64x64.png",
            rows=8,
            cols=7,
            connect=9,
        ),
    },
    "en": {
        GameTypeId.XO: GameCatalogEntry(
            title="XO GAME | TIC TAC TOE",
            id=GameTypeId.XO,
            description="❌⭕️ The classic game of Tic Tac Toe, also known as XO ❌⭕️",
            thumb_url="https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Tic_tac_toe.svg/1200px-Tic_tac_toe.svg.png",
            rows=3,
            cols=3,
            connect=3,
        ),
        GameTypeId.CONNECT_3: GameCatalogEntry(
            title="CONNECT 3 | CONNECT 3 AND WIN!",
            id=GameTypeId.CONNECT_3,
            description="🥇 All you need to do is line up 3 of your pieces in a row — horizontally, vertically, or diagonally 🥇",
            thumb_url="https://lh6.googleusercontent.com/proxy/TYpZrjlqu_tnJvoNtKQHNZXwlxuCbZxEsO_Aq09iS5KAcUDKPaU9mHlr6pLl5Nvyk28rd6y_JoL4aqrxZ0tRQgSKT0ewVMAybrqk20W-UznJCA22AfUyVyTcHm2rRnh18Fa3K5PIXYgSaVs",
            rows=6,
            cols=7,
            connect=3,
        ),
        GameTypeId.CONNECT_4: GameCatalogEntry(
            title="CONNECT 4 | CONNECT 4 AND WIN!",
            id=GameTypeId.CONNECT_4,
            description="🥇 All you need to do is line up 4 of your pieces in a row — horizontally, vertically, or diagonally 🥇",
            thumb_url="https://www.researchgate.net/profile/Gaetan-Sanchez/publication/258381798/figure/fig1/AS:311148797808643@1451195062476/Traditional-Connect-Four-Here-Red-wins-with-four-coins-aligned-diagonally.png",
            rows=6,
            cols=7,
            connect=4,
        ),
        GameTypeId.CONNECT_5: GameCatalogEntry(
            title="CONNECT 5 | CONNECT 5 AND WIN!",
            id=GameTypeId.CONNECT_5,
            description="🥇 All you need to do is line up 5 of your pieces in a row — horizontally, vertically, or diagonally 🥇",
            thumb_url="https://static.drimify.com/wp-content/uploads/2024/12/screenshot-415-min.png",
            rows=8,
            cols=8,
            connect=5,
        ),
        GameTypeId.MINE: GameCatalogEntry(
            title="MINEROB | MINESWEEPER",
            id=GameTypeId.MINE,
            description="💣 Turn-based two-player minesweeper — reveal cells and collect points! 💣",
            thumb_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Minesweeper_64x64.png/240px-Minesweeper_64x64.png",
            rows=8,
            cols=7,
            connect=9,
        ),
    },
    "tr": {
        GameTypeId.XO: GameCatalogEntry(
            title="XO GAME | TIK TAK TOZ",
            id=GameTypeId.XO,
            description="❌⭕️ Klasik XO (Tic Tac Toe) oyunu ❌⭕️",
            thumb_url="https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Tic_tac_toe.svg/1200px-Tic_tac_toe.svg.png",
            rows=3,
            cols=3,
            connect=3,
        ),
        GameTypeId.CONNECT_3: GameCatalogEntry(
            title="CONNECT 3 | 3'LÜ BAĞLA!",
            id=GameTypeId.CONNECT_3,
            description="🥇 3 taşını yatay, dikey veya çapraz diz — kazan! 🥇",
            thumb_url="https://lh6.googleusercontent.com/proxy/TYpZrjlqu_tnJvoNtKQHNZXwlxuCbZxEsO_Aq09iS5KAcUDKPaU9mHlr6pLl5Nvyk28rd6y_JoL4aqrxZ0tRQgSKT0ewVMAybrqk20W-UznJCA22AfUyVyTcHm2rRnh18Fa3K5PIXYgSaVs",
            rows=6,
            cols=7,
            connect=3,
        ),
        GameTypeId.CONNECT_4: GameCatalogEntry(
            title="CONNECT 4 | 4'LÜ BAĞLA!",
            id=GameTypeId.CONNECT_4,
            description="🥇 4 taşını yatay, dikey veya çapraz diz — kazan! 🥇",
            thumb_url="https://www.researchgate.net/profile/Gaetan-Sanchez/publication/258381798/figure/fig1/AS:311148797808643@1451195062476/Traditional-Connect-Four-Here-Red-wins-with-four-coins-aligned-diagonally.png",
            rows=6,
            cols=7,
            connect=4,
        ),
        GameTypeId.CONNECT_5: GameCatalogEntry(
            title="CONNECT 5 | 5'Lİ BAĞLA!",
            id=GameTypeId.CONNECT_5,
            description="🥇 5 taşını yatay, dikey veya çapraz diz — kazan! 🥇",
            thumb_url="https://static.drimify.com/wp-content/uploads/2024/12/screenshot-415-min.png",
            rows=8,
            cols=8,
            connect=5,
        ),
        GameTypeId.MINE: GameCatalogEntry(
            title="MINEROB | MAYIN TARA",
            id=GameTypeId.MINE,
            description="💣 İki kişilik sıra tabanlı mayın tarlası — hücreleri aç, puan topla! 💣",
            thumb_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Minesweeper_64x64.png/240px-Minesweeper_64x64.png",
            rows=8,
            cols=7,
            connect=9,
        ),
    },
}


class GameCatalogService:
    def list_for_lang(self, lang: str) -> list[GameCatalogEntry]:
        catalog = GAME_CATALOG.get(lang, GAME_CATALOG["en"])
        return list(catalog.values())

    def get(self, lang: str, game_type: GameTypeId) -> GameCatalogEntry:
        catalog = GAME_CATALOG.get(lang, GAME_CATALOG["en"])
        return catalog[game_type]
