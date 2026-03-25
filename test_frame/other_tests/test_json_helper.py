import json
import threading
from datetime import date, datetime

from funboost.utils.json_helper import dict_to_un_strict_json_deep


class CustomObj:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f"CustomObj(name={self.name})"

    __repr__ = __str__


def test_dict_to_un_strict_json_deep_with_complex_nested_data():
    complex_dict = {
        "level1": {
            "level2": {
                "list_items": [
                    {"dt": datetime(2026, 3, 24, 12, 34, 56), "today": date(2026, 3, 24)},
                    {"custom": CustomObj("alpha"), "bytes_data": b"abc"},
                    {"set_data": {1, 2, 3}, "frozenset_data": frozenset({"x", "y"})},
                    {"lock": threading.Lock()},
                ],
                ("tuple_key", 1): {
                    "nested_tuple": (CustomObj("beta"), {"inner_set": {CustomObj("gamma"), 1}})
                },
            }
        },
        "top_tuple": (1, 2, {"k": CustomObj("top")}),
        None: {"none_key_ok": True},
        123: {"int_key_ok": "yes"},
    }

    json_text = dict_to_un_strict_json_deep(complex_dict, indent=2)
    parsed = json.loads(json_text)

    assert parsed["level1"]["level2"]["list_items"][0]["dt"] == "2026-03-24 12:34:56"
    assert parsed["level1"]["level2"]["list_items"][0]["today"] == "2026-03-24"
    assert parsed["level1"]["level2"]["list_items"][1]["custom"] == "CustomObj(name=alpha)"
    assert parsed["level1"]["level2"]["list_items"][1]["bytes_data"] == "b'abc'"
    assert set(parsed["level1"]["level2"]["list_items"][2]["set_data"]) == {1, 2, 3}
    assert set(parsed["level1"]["level2"]["list_items"][2]["frozenset_data"]) == {"x", "y"}
    assert "lock object" in parsed["level1"]["level2"]["list_items"][3]["lock"]

    tuple_key_str = "('tuple_key', 1)"
    assert tuple_key_str in parsed["level1"]["level2"]
    nested_tuple = parsed["level1"]["level2"][tuple_key_str]["nested_tuple"]
    assert isinstance(nested_tuple, list)
    assert nested_tuple[0] == "CustomObj(name=beta)"
    assert 1 in nested_tuple[1]["inner_set"]
    assert "CustomObj(name=gamma)" in nested_tuple[1]["inner_set"]

    assert parsed["top_tuple"][2]["k"] == "CustomObj(name=top)"
    assert parsed["null"]["none_key_ok"] is True
    assert parsed["123"]["int_key_ok"] == "yes"

    print("dict_to_un_strict_json_deep 深层级复杂结构测试通过")


if __name__ == "__main__":
    test_dict_to_un_strict_json_deep_with_complex_nested_data()