from pathlib import Path

from bot.config.i18n import I18nConfigClass
from bot.domain.schemas.texts import CommandKey, LocaleTexts, TextsBundle


class TextsService:
    def __init__(self, config: I18nConfigClass) -> None:
        self._config = config
        self._bundle = self._load()

    def _load(self) -> TextsBundle:
        raw = Path(self._config.texts_path).read_text(encoding="utf-8")
        import json

        data = json.loads(raw)
        return TextsBundle.model_validate(data)

    @property
    def langs(self) -> list[str]:
        return self._bundle.langs

    def resolve_lang(self, lang_code: str | None) -> str:
        if lang_code and lang_code in self._bundle.langs:
            return lang_code
        if self._config.default_lang in self._bundle.langs:
            return self._config.default_lang
        return "en"

    def texts_for(self, lang: str) -> LocaleTexts:
        return self._bundle.for_lang(lang)

    def get(self, lang: str, key: CommandKey) -> str:
        return self.texts_for(lang).get(key)
