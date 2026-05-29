from __future__ import annotations

import json
import unittest
from pathlib import Path

from bot.domain.schemas.texts import CommandKey, LocaleTexts, TextsBundle


class TextsSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = Path("src/texts.json").read_text(encoding="utf-8")
        cls.bundle = TextsBundle.model_validate(json.loads(raw))

    def test_langs_match_file(self) -> None:
        self.assertEqual(set(self.bundle.langs), {"fa", "en", "ru"})

    def test_locale_texts_use_kebab_aliases(self) -> None:
        en = self.bundle.for_lang("en")
        self.assertIn("Welcome", en.start)
        self.assertEqual(en.get(CommandKey.COLUMN_FULL), en.column_full)

    def test_for_lang_fallback_to_english(self) -> None:
        unknown = self.bundle.for_lang("zz")
        self.assertEqual(unknown.start, self.bundle.for_lang("en").start)

    def test_command_key_getter(self) -> None:
        fa: LocaleTexts = self.bundle.for_lang("fa")
        self.assertTrue(fa.get(CommandKey.LANG_CHANGED))
