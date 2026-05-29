from __future__ import annotations

import unittest

from aiogram.utils.i18n import I18n

import bot.i18n_bootstrap  # noqa: F401
from bot.config.i18n import I18nConfigClass
from bot.infrastructure.i18n.translator import Translator
from bot.locales.i18n_keys import I18nKeys


class I18nCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import subprocess

        subprocess.run(["poetry", "run", "poe", "compile"], check=True)
        i18n = I18n.get_current()
        assert i18n is not None
        cls.translator = Translator(I18nConfigClass(), i18n)

    def test_supported_langs(self) -> None:
        self.assertEqual(set(self.translator.supported_langs), {"tr", "en", "fa"})

    def test_english_start_message(self) -> None:
        text = self.translator.t(I18nKeys.START, "en")
        self.assertIn("Welcome", text)

    def test_turkish_start_message(self) -> None:
        text = self.translator.t(I18nKeys.START, "tr")
        self.assertIn("hoş geldiniz", text)

    def test_persian_start_message(self) -> None:
        text = self.translator.t(I18nKeys.START, "fa")
        self.assertIn("خوش", text)

    def test_unknown_lang_falls_back_to_default(self) -> None:
        resolved = self.translator.resolve_lang("zz")
        self.assertEqual(resolved, "fa")
