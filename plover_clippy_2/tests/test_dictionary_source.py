import builtins
import sys
import types
import unittest
from unittest.mock import patch

from plover_clippy_2.dictionary_source import (
    dictionaries_for_phrase,
    dictionary_for_translation,
    dictionary_suffix,
)
from plover_clippy_2 import install_sqlite


class Translation:
    def __init__(self, rtfcre):
        self.rtfcre = rtfcre


class Dictionary:
    def __init__(self, path, entries, enabled=True):
        self.path = path
        self.enabled = enabled
        self._entries = entries

    def get(self, outline):
        return self._entries.get(outline)


class Engine:
    def __init__(self, table):
        self.table = table

    def lookup_from_all(self, outline):
        return self.table.get(outline)


class Collection:
    def __init__(self, dicts):
        self.dicts = dicts


class EngineWithoutLookup:
    def __init__(self, dicts):
        self.dictionaries = Collection(dicts)


class DictionarySourceTest(unittest.TestCase):
    def test_first_enabled_dictionary_wins(self):
        outline = ("TH", "S")
        engine = Engine({
            outline: [
                ("this is", Dictionary(r"C:\plover\user.json", {})),
                ("this is", Dictionary("asset:plover:assets/main.json", {})),
            ],
        })
        name = dictionary_for_translation(engine, Translation(outline))
        self.assertEqual(name, "user.json")

    def test_deleted_entry_hides_lower_dictionaries(self):
        outline = ("TEFT",)
        engine = Engine({
            outline: [
                ("{plover:deleted}", Dictionary("user.json", {})),
                ("test", Dictionary("main.json", {})),
            ],
        })
        self.assertEqual(
            dictionary_for_translation(engine, Translation(outline)),
            "",
        )

    def test_phrase_collapses_consecutive_names(self):
        user = ("TEFT",)
        main = ("W", "EU")
        engine = Engine({
            user: [("test", Dictionary("user.json", {}))],
            main: [("we", Dictionary("/dicts/main.json", {}))],
        })
        phrase = [
            Translation(user),
            Translation(("TEFT",)),
            Translation(main),
        ]
        self.assertEqual(dictionaries_for_phrase(engine, phrase), "user.json, main.json")
        self.assertEqual(dictionary_suffix("user.json, main.json"), " (user.json, main.json)")
        self.assertEqual(dictionary_suffix(""), "")

    def test_string_outline_and_collection_fallback(self):
        outline = ("KAT",)
        engine = EngineWithoutLookup([
            Dictionary("disabled.json", {outline: "cat"}, enabled=False),
            Dictionary("commands.json", {outline: "cat"}),
        ])
        name = dictionary_for_translation(engine, Translation("KAT"))
        self.assertEqual(name, "commands.json")

    def test_sqlite_shim_registers_pysqlite3(self):
        fake = types.ModuleType("pysqlite3")
        fake.connect = lambda: None

        real_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "sqlite3":
                raise ModuleNotFoundError(name)
            if name == "pysqlite3":
                return fake
            return real_import(name, globals, locals, fromlist, level)

        saved = sys.modules.pop("sqlite3", None)
        try:
            with patch("builtins.__import__", fake_import):
                module = install_sqlite()
            self.assertIs(module, fake)
            self.assertIs(sys.modules["sqlite3"], fake)
        finally:
            if saved is not None:
                sys.modules["sqlite3"] = saved
            else:
                sys.modules.pop("sqlite3", None)


if __name__ == "__main__":
    unittest.main()
