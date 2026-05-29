from __future__ import annotations

from aiogram.utils.i18n import I18n
from aiogram.utils.i18n import gettext as _

from bot.config.i18n import I18nConfigClass
from bot.locales.i18n_keys import I18nKeys


class Translator:
    """Typed wrapper around aiogram I18n with explicit locale support."""

    def __init__(self, config: I18nConfigClass, i18n: I18n | None = None) -> None:
        self._config = config
        self._i18n = i18n or I18n.get_current()

    @property
    def supported_langs(self) -> list[str]:
        return self._config.supported_langs

    def resolve_lang(self, lang_code: str | None) -> str:
        if lang_code and lang_code in self._config.supported_langs:
            return lang_code
        return self._config.default_lang

    def t(self, key: I18nKeys, locale: str, **kwargs: object) -> str:
        if self._i18n is None:
            msg = "I18n is not initialized"
            raise RuntimeError(msg)
        with self._i18n.use_locale(locale):
            text = self._i18n.gettext(key.value)
        return text.format(**kwargs) if kwargs else text

    def current(self, key: I18nKeys, **kwargs: object) -> str:
        text = _(key.value)
        return text.format(**kwargs) if kwargs else text
