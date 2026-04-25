#!/usr/bin/env python3
"""Translate keymap-drawer legends to de-DE output characters.

This module intentionally avoids external YAML dependencies and performs a
targeted in-place rewrite for keymap-drawer's generated YAML style.
"""

from __future__ import annotations

from pathlib import Path
import re


# keymap-drawer legend -> de-DE resulting character
#
# Two kinds of entries:
# 1. Legacy: keymap-drawer renders standard ZMK keycodes and we fix them
#    (e.g. ";" -> "ö" because SEMI on DE layout is ö)
# 2. DE_* locale names: keymap-drawer passes them through literally
#    (e.g. "DE_O_UMLAUT" -> "ö")
DE_LEGEND_MAP = {
    # --- Legacy mappings (standard ZMK keycode legends) ---
    "Sft+!": "!",
    'Sft+"': '"',
    "Sft+$": "$",
    "Sft+%": "%",
    "Sft+&": "&",
    "Sft+7": "/",
    "Sft+8": "(",
    "Sft+9": ")",
    "Sft+\\": ">",
    "AltGr+7": "{",
    "AltGr+8": "[",
    "AltGr+9": "]",
    "AltGr+0": "}",
    "AltGr+-": "\\",
    "AltGr+\\": "|",
    "\\": "<",
    "[": "ü",
    ";": "ö",
    # NOTE: "'" (SQT) -> "ä" removed; we now use DE_A_UMLAUT explicitly.
    # Keeping this would misinterpret shifted "'" (single quote) as "ä".
    "-": "ß",
    "/": "-",
    # --- DE_* locale name mappings ---
    # Letters
    "DE_A": "a",
    "DE_B": "b",
    "DE_C": "c",
    "DE_D": "d",
    "DE_E": "e",
    "DE_F": "f",
    "DE_G": "g",
    "DE_H": "h",
    "DE_I": "i",
    "DE_J": "j",
    "DE_K": "k",
    "DE_L": "l",
    "DE_M": "m",
    "DE_N": "n",
    "DE_O": "o",
    "DE_P": "p",
    "DE_Q": "q",
    "DE_R": "r",
    "DE_S": "s",
    "DE_T": "t",
    "DE_U": "u",
    "DE_V": "v",
    "DE_W": "w",
    "DE_X": "x",
    "DE_Y": "y",
    "DE_Z": "z",
    # Digits (keymap-drawer may render DE_N7 as "DE 7" or "DE N7")
    "DE_N0": "0",
    "DE_N1": "1",
    "DE_N2": "2",
    "DE_N3": "3",
    "DE_N4": "4",
    "DE_N5": "5",
    "DE_N6": "6",
    "DE_N7": "7",
    "DE_N8": "8",
    "DE_N9": "9",
    "DE_0": "0",
    "DE_1": "1",
    "DE_2": "2",
    "DE_3": "3",
    "DE_4": "4",
    "DE_5": "5",
    "DE_6": "6",
    "DE_7": "7",
    "DE_8": "8",
    "DE_9": "9",
    # Umlauts and ß
    "DE_A_UMLAUT": "ä",
    "DE_O_UMLAUT": "ö",
    "DE_U_UMLAUT": "ü",
    "DE_SHARP_S": "ß",
    "DE_ESZETT": "ß",
    "DE_SZ": "ß",
    # Punctuation
    "DE_COMMA": ",",
    "DE_DOT": ".",
    "DE_PERIOD": ".",
    "DE_COLON": ":",
    "DE_SEMI": ";",
    "DE_SEMICOLON": ";",
    "DE_EXCL": "!",
    "DE_EXCLAMATION": "!",
    "DE_QMARK": "?",
    "DE_QUESTION": "?",
    "DE_DQT": '"',
    "DE_DOUBLE_QUOTES": '"',
    "DE_SQT": "'",
    "DE_SINGLE_QUOTE": "'",
    "DE_APOSTROPHE": "'",
    "DE_APOS": "'",
    # Arithmetic / symbols
    "DE_PLUS": "+",
    "DE_MINUS": "-",
    "DE_ASTRK": "*",
    "DE_ASTERISK": "*",
    "DE_STAR": "*",
    "DE_FSLH": "/",
    "DE_SLASH": "/",
    "DE_EQUAL": "=",
    "DE_UNDER": "_",
    "DE_UNDERSCORE": "_",
    # Brackets
    "DE_LPAR": "(",
    "DE_LEFT_PARENTHESIS": "(",
    "DE_RPAR": ")",
    "DE_RIGHT_PARENTHESIS": ")",
    "DE_LBKT": "[",
    "DE_LEFT_BRACKET": "[",
    "DE_RBKT": "]",
    "DE_RIGHT_BRACKET": "]",
    "DE_LBRC": "{",
    "DE_LEFT_BRACE": "{",
    "DE_RBRC": "}",
    "DE_RIGHT_BRACE": "}",
    "DE_LT": "<",
    "DE_LESS_THAN": "<",
    "DE_GT": ">",
    "DE_GREATER_THAN": ">",
    # Special characters
    "DE_AT": "@",
    "DE_AT_SIGN": "@",
    "DE_HASH": "#",
    "DE_POUND": "#",
    "DE_DLLR": "$",
    "DE_DOLLAR": "$",
    "DE_PRCNT": "%",
    "DE_PERCENT": "%",
    "DE_AMPS": "&",
    "DE_AMPERSAND": "&",
    "DE_PIPE": "|",
    "DE_BSLH": "\\",
    "DE_BACKSLASH": "\\",
    "DE_TILDE": "~",
    "DE_CARET": "^",
    "DE_GRAVE": "`",
    "DE_ACUTE": "´",
    "DE_DEG": "°",
    "DE_DEGREE": "°",
    "DE_SECT": "§",
    "DE_SECTION": "§",
    "DE_EURO": "€",
    "DE_MU": "µ",
    "DE_MICRO": "µ",
    "DE_SUPER2": "²",
    "DE_SQUARE": "²",
    "DE_SUPER3": "³",
    "DE_CUBE": "³",
    # Macro / behavior display names
    "&bktk": "`",
    "&tbtk": "```",
    "&mod_bt": "`",
    "&grimacing": "😬",
    "&uc 0x1F62C 0": "😬",
    "&uc 0x1F600 0": "😀",
}


def translate_legend_de(label: str) -> str:
    """Translate one rendered legend label to de-DE output."""
    uc_match = re.match(r"^&uc\s+0x([0-9A-Fa-f]+)\s+0$", label)
    if uc_match:
        codepoint = int(uc_match.group(1), 16)
        if 0 <= codepoint <= 0x10FFFF:
            return chr(codepoint)

    result = DE_LEGEND_MAP.get(label)
    if result is not None:
        return result
    # keymap-drawer renders DE_FOO_BAR as "DE FOO BAR" (spaces instead of underscores)
    underscore_key = label.replace(" ", "_")
    result = DE_LEGEND_MAP.get(underscore_key)
    if result is not None:
        return result
    return label


def _quote_single(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _parse_scalar(token: str) -> tuple[str, bool, str]:
    stripped = token.strip()
    if stripped.startswith("'") and stripped.endswith("'") and len(stripped) >= 2:
        return stripped[1:-1].replace("''", "'"), True, "'"
    if stripped.startswith('"') and stripped.endswith('"') and len(stripped) >= 2:
        return stripped[1:-1], True, '"'
    return stripped, False, ""


def _translate_scalar_token(token: str) -> str:
    value, was_quoted, _ = _parse_scalar(token)
    translated = translate_legend_de(value)
    if translated == value:
        return token
    return _quote_single(translated)


def _split_inline_list(content: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False

    for ch in content:
        if ch == "'" and not in_double:
            in_single = not in_single
            current.append(ch)
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            current.append(ch)
            continue
        if ch == "," and not in_single and not in_double:
            items.append("".join(current).strip())
            current = []
            continue
        current.append(ch)

    tail = "".join(current).strip()
    if tail:
        items.append(tail)
    return items


def _translate_inline_list_item(token: str) -> str:
    translated = _translate_scalar_token(token)
    value, _, _ = _parse_scalar(translated)
    shifted = DE_SHIFT_MAP.get(value)
    if shifted:
        return "{{t: {}, s: {}}}".format(_quote_single(value), _quote_single(shifted))
    return translated


def _translate_inline_list_line(line: str) -> str:
    start = line.find("[")
    end = line.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return line
    inner = line[start + 1 : end]
    items = _split_inline_list(inner)
    translated_items = [_translate_inline_list_item(item) for item in items]
    return f"{line[: start + 1]}{', '.join(translated_items)}{line[end:]}"


def _translate_inline_map_fields(line: str) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        value = match.group(2)
        return f"{key}{_translate_scalar_token(value)}"

    line = re.sub(r"(\bt:\s*)([^,}]+)", repl, line)
    line = re.sub(r"(\bh:\s*)([^,}]+)", repl, line)
    line = re.sub(r"(\bs:\s*)([^,}]+)", repl, line)
    line = re.sub(r"(\bk:\s*)([^,}]+)", repl, line)
    return line


DE_SHIFT_MAP = {
    ",": ";",
    ".": ":",
    "-": "_",
    "ß": "?",
    "^": "°",
    "´": "`",
    "#": "'",
    "1": "!",
    "2": '"',
    "3": "§",
    "4": "$",
    "5": "%",
    "6": "&",
    "7": "/",
    "8": "(",
    "9": ")",
    "0": "=",
    "+": "*",
    "`": "```",
}


def _inject_shifted_label(line: str) -> str:
    if re.search(r"\bs:", line):
        return line

    m = re.search(r"\{[^}]*\bt:\s*([^,}]+)", line)
    if m:
        tap_token = m.group(1).strip()
        tap_value, _, _ = _parse_scalar(tap_token)
        shifted = DE_SHIFT_MAP.get(tap_value)
        if shifted:
            insert_pos = m.end()
            s_field = f", s: {_quote_single(shifted)}"
            return line[:insert_pos] + s_field + line[insert_pos:]
        return line

    block_m = re.match(r"^(\s*-\s+)(.+)$", line)
    if block_m:
        prefix = block_m.group(1)
        rest = block_m.group(2).rstrip()
        if rest.startswith("{") or rest.startswith("["):
            return line
        value, _, _ = _parse_scalar(rest)
        shifted = DE_SHIFT_MAP.get(value)
        if shifted:
            return f"{prefix}{{t: {_quote_single(value)}, s: {_quote_single(shifted)}}}"

    return line


LAYER_INDEX_MAP = {
    "2": "Nav",
}


def _fix_layer_indices(yaml_text: str) -> str:
    lines = yaml_text.splitlines()
    out: list[str] = []
    for line in lines:
        for idx, name in LAYER_INDEX_MAP.items():
            pattern = f"  '{idx}':"
            if line.startswith(pattern):
                line = f"  {name}:" + line[len(pattern) :]
                break
        for idx, name in LAYER_INDEX_MAP.items():
            m = re.match(rf"^(\s*-\s+)'{idx}'(\s*)$", line)
            if m:
                line = f"{m.group(1)}{name}{m.group(2)}"
                break
            m = re.match(rf"^(\s*-\s+){idx}(\s*)$", line)
            if m:
                line = f"{m.group(1)}{name}{m.group(2)}"
                break
        out.append(line)
    return "\n".join(out)


def translate_keymap_yaml_de(yaml_text: str) -> str:
    yaml_text = _fix_layer_indices(yaml_text)

    out_lines: list[str] = []
    for line in yaml_text.splitlines():
        translated = line

        if "- [" in translated and "]" in translated:
            translated = _translate_inline_list_line(translated)

        translated = _translate_inline_map_fields(translated)

        block_item = re.match(r"^(\s*-\s+)([^#\n]+)$", translated)
        if block_item:
            prefix = block_item.group(1)
            value = block_item.group(2).rstrip()
            stripped = value.strip()
            if (
                stripped
                and not stripped.startswith("{")
                and not stripped.startswith("[")
            ):
                translated_value = _translate_scalar_token(stripped)
                translated = f"{prefix}{translated_value}"

        translated = _inject_shifted_label(translated)
        out_lines.append(translated)

    return "\n".join(out_lines) + "\n"


def translate_keymap_yaml_file_de(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    translated = translate_keymap_yaml_de(original)
    path.write_text(translated, encoding="utf-8")
