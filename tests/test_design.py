import re
from pathlib import Path


def test_design_runtime_color_mapping():
    design = Path("DESIGN.md").read_text(encoding="utf-8")
    css = Path("web/styles.css").read_text(encoding="utf-8")
    mapping = {
        "primary": "ink",
        "text": "text",
        "muted": "muted",
        "background": "paper",
        "surface": "surface",
        "border": "line",
        "accent": "accent",
        "tint": "tint",
        "success": "success",
        "warning": "warning",
        "danger": "danger",
    }
    for key, var in mapping.items():
        expected = re.search(rf"^  {key}: '(#[a-f0-9]+)'", design, re.M).group(1)
        actual = re.search(rf"--{var}:\s*(#[a-f0-9]+)", css).group(1)
        if len(actual) == 4:
            actual = "#" + "".join(x * 2 for x in actual[1:])
        assert actual == expected
