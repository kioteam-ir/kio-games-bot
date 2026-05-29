from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, RootModel


class CommandKey(StrEnum):
    START = "start"
    CREATE_GAME_TEXT = "create-game-text"
    CREATE_GAME_BUTTON = "create-game-button"
    YOU_ARE_BANNED_TITLE = "you-are-banned-title"
    YOU_ARE_BANNED_TEXT = "you-are-banned-text"
    WAITING_FOR_PLAYER = "waiting-for-player"
    IPLAY = "i-play"
    CANNOT_PLAY_WITH_YOURSELF = "cannot-play-with-yourself"
    NOT_YOUR_GAME = "not-your-game"
    NOT_YOUR_TURN = "not-your-turn"
    COLUMN_FULL = "column-full"
    PLAYER_GAME_STATS = "player-game-stats"
    GAME_IN_PROGRESS_TEXT = "game-in-progress-text"
    GAME_ENDED_TEXT = "game-ended-text"
    GAME_IS_DRAW_TEXT = "game-is-draw-text"
    GAME = "game"
    PLAY_WITH_COOL_PEOPLE_BUTTON = "play-with-cool-people-button"
    PLAY_WITH_COOL_PEOPLE_TEXT = "play-with-cool-people-text"
    GAME_STOPPED = "game-stopped"
    LANG_CHANGED = "lang-changed"
    CHANGE_YOUR_LANG = "change-your-lang"
    CHANGE_YOUR_LANG_TEXT = "change-your-lang-text"
    JOIN_FIRST = "join-first"


class LocaleTexts(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    start: str
    create_game_text: str = Field(alias="create-game-text")
    create_game_button: str = Field(alias="create-game-button")
    you_are_banned_title: str = Field(alias="you-are-banned-title")
    you_are_banned_text: str = Field(alias="you-are-banned-text")
    waiting_for_player: str = Field(alias="waiting-for-player")
    iplay: str = Field(alias="i-play")
    cannot_play_with_yourself: str = Field(alias="cannot-play-with-yourself")
    not_your_game: str = Field(alias="not-your-game")
    not_your_turn: str = Field(alias="not-your-turn")
    column_full: str = Field(alias="column-full")
    player_game_stats: str = Field(alias="player-game-stats")
    game_in_progress_text: str = Field(alias="game-in-progress-text")
    game_ended_text: str = Field(alias="game-ended-text")
    game_is_draw_text: str = Field(alias="game-is-draw-text")
    game: str
    play_with_cool_people_button: str = Field(alias="play-with-cool-people-button")
    play_with_cool_people_text: str = Field(alias="play-with-cool-people-text")
    game_stopped: str = Field(alias="game-stopped")
    lang_changed: str = Field(alias="lang-changed")
    change_your_lang: str = Field(alias="change-your-lang")
    change_your_lang_text: str = Field(alias="change-your-lang-text")
    join_first: str = Field(alias="join-first")

    def get(self, key: CommandKey) -> str:
        return getattr(self, key.name.lower())


class TextsBundle(RootModel[dict[str, LocaleTexts]]):
    model_config = ConfigDict(frozen=True)

    @property
    def langs(self) -> list[str]:
        return list(self.root.keys())

    def for_lang(self, lang: str) -> LocaleTexts:
        if lang in self.root:
            return self.root[lang]
        return self.root["en"]
