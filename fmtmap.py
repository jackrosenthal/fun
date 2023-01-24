import subprocess
import sys
import string
import unicodedata

result = subprocess.run(
    ['gcc', '-dM', '-E', '/usr/include/linux/input-event-codes.h'],
    check=True,
    stdout=subprocess.PIPE,
    encoding='utf-8',
)

name_to_keycodes = {}
for line in result.stdout.splitlines():
    if line.startswith('#define KEY_'):
        words = line.split()
        if len(words) != 3:
            continue
        try:
            keycode = int(words[2], base=0)
        except ValueError:
            continue
        name_to_keycodes[words[1]] = keycode


rows = [
    #(
    #    "Function Row",
    #    [
    #        "KEY_ESC",
    #        "KEY_F1",
    #        "KEY_F2",
    #        "KEY_F3",
    #        "KEY_F4",
    #        "KEY_F5",
    #        "KEY_F6",
    #        "KEY_F7",
    #        "KEY_F8",
    #        "KEY_F9",
    #        "KEY_F10",
    #        "KEY_F11",
    #        "KEY_F12",
    #    ],
    #),
    (
        "Number Row",
        [
            #"KEY_GRAVE",
            "KEY_1",
            "KEY_2",
            "KEY_3",
            "KEY_4",
            "KEY_5",
            "KEY_6",
            "KEY_7",
            "KEY_8",
            "KEY_9",
            "KEY_0",
            #"KEY_MINUS",
            #"KEY_EQUAL",
            "KEY_BACKSPACE",
        ],
    ),
    (
        "Top Row",
        [
            "KEY_TAB",
            "KEY_Q",
            "KEY_W",
            "KEY_E",
            "KEY_R",
            "KEY_T",
            "KEY_Y",
            "KEY_U",
            "KEY_I",
            "KEY_O",
            "KEY_P",
            #"KEY_LEFTBRACE",
            #"KEY_RIGHTBRACE",
            #"KEY_BACKSLASH",
        ],
    ),
    (
        "Home Row",
        [
            "KEY_CAPSLOCK",
            "KEY_LEFTMETA",
            "KEY_A",
            "KEY_S",
            "KEY_D",
            "KEY_F",
            "KEY_G",
            "KEY_H",
            "KEY_J",
            "KEY_K",
            "KEY_L",
            "KEY_SEMICOLON",
            "KEY_APOSTROPHE",
            #"KEY_ENTER",
        ],
    ),
    (
        "Bottom Row",
        [
            "KEY_LEFTSHIFT",
            "KEY_Z",
            "KEY_X",
            "KEY_C",
            "KEY_V",
            "KEY_B",
            "KEY_N",
            "KEY_M",
            "KEY_COMMA",
            "KEY_DOT",
            "KEY_SLASH",
            "KEY_RIGHTSHIFT",
        ],
    ),
    (
        "Spacebar Row",
        [
            "KEY_LEFTCTRL",
            "KEY_LEFTALT",
            #"KEY_SPACE",
            "KEY_RIGHTALT",
            "KEY_RIGHTCTRL",
        ],
    ),
]


mod_values = {
    'plain': 0,
    'shift': 1,
    'altgr': 2,
    'control': 4,
    'alt': 8,
    'shiftl': 16,
    'shiftr': 32,
    'ctrll': 64,
}


def modlist(idx):
    mods = []
    mod_val_rev = sorted(mod_values.items(), key=lambda t: -t[1])
    # plain
    mod_val_rev.pop()
    for mod_name, mod_val in mod_val_rev:
        if idx >= mod_val:
            idx -= mod_val
            mods.append(mod_name)
    return mods


prelude = []
key_defs = {}
keytrans_defs = {
    "U+{:04x}".format(ord(letter)): name
    for letter, name in (
            ("0", "zero"),
            ("1", "one"),
            ("2", "two"),
            ("3", "three"),
            ("4", "four"),
            ("5", "five"),
            ("6", "six"),
            ("7", "seven"),
            ("8", "eight"),
            ("9", "nine"),
            ("+", "plus"),
            ("/", "slash"),
            ("\\", "backslash"),
            ("%", "percent"),
            ("$", "dollar"),
            ("?", "question"),
            ("(", "parenleft"),
            (")", "parenright"),
            ("'", "apostrophe"),
            ("*", "asterisk"),
            ("#", "numbersign"),
            ("&", "ampersand"),
            ("{", "braceleft"),
            ("}", "braceright"),
            ("-", "minus"),
            ("_", "underscore"),
            ('"', "quotedbl"),
            (",", "comma"),
            (".", "period"),
            ("|", "bar"),
            ("[", "bracketleft"),
            ("]", "bracketright"),
            ("^", "asciicircum"),
            ("~", "asciitilde"),
            ("!", "exclam"),
            ("<", "less"),
            (">", "greater"),
            ("=", "equal"),
            ("`", "grave"),
            ("@", "at"),
            (" ", "space"),
            (";", "semicolon"),
            (":", "colon"),
    )
}

for letter in string.ascii_letters:
    keytrans_defs["U+{:04x}".format(ord(letter))] = letter

def keytrans(keysym):
    # don't care about caps state
    if keysym.startswith("+"):
        keysym = keysym[1:]
    return keytrans_defs.get(keysym, keysym)

for line in sys.stdin:
    line, _, _ = line.partition('#')
    line_parts = line.split()
    if not line_parts:
        continue
    if line_parts[0] in mod_values:
        modval = 0
        while line_parts[0] in mod_values:
            modval += mod_values[line_parts[0]]
            line_parts = line_parts[1:]
        assert line_parts[0] == "keycode"
        keycode = int(line_parts[1])
        assert line_parts[2] == "="
        line_parts = line_parts[3:]
        assert len(line_parts) == 1
        keysym = line_parts[0]
        if keycode in key_defs:
            columns = key_defs[keycode]
        else:
            columns = ["VoidSymbol" for _ in range(128)]
        columns[modval] = keytrans(keysym)
        key_defs[keycode] = columns
        continue
    if line_parts[0] != "keycode":
        prelude.append(' '.join(line_parts))
        continue
    keycode = int(line_parts[1])
    assert line_parts[2] == '='
    key_defs[keycode] = [keytrans(keysym) for keysym in line_parts[3:]]


key_defs[name_to_keycodes["KEY_SLASH"]] = ["CtrlL"] * 128
key_defs[name_to_keycodes["KEY_BACKSPACE"]] = ["BackSpace"] * 128
key_defs[name_to_keycodes["KEY_TAB"]] = ["Escape"] * 128
key_defs[name_to_keycodes["KEY_LEFTMETA"]] = key_defs[name_to_keycodes["KEY_CAPSLOCK"]]
curnum_defs = {
    # Cursor control
    "KEY_Q": "PageUp",
    "KEY_W": "BackSpace",
    "KEY_E": "Up",
    "KEY_R": "Delete",
    "KEY_T": "PageDown",
    "KEY_A": "Home",
    "KEY_S": "Left",
    "KEY_D": "Down",
    "KEY_F": "Right",
    "KEY_G": "End",

    # Numpad
    "KEY_U": "one",
    "KEY_I": "two",
    "KEY_O": "three",
    "KEY_J": "four",
    "KEY_K": "five",
    "KEY_L": "six",
    "KEY_N": "zero",
    "KEY_M": "seven",
    "KEY_COMMA": "eight",
    "KEY_DOT": "nine",

    # Numpad Extras
    "KEY_H": "period",
    "KEY_Z": "slash",
    "KEY_X": "asterisk",
    "KEY_C": "minus",
    "KEY_V": "plus",
    "KEY_B": "comma",
}
for keyname, keyval in curnum_defs.items():
    key_defs[name_to_keycodes[keyname]][mod_values["ctrll"]] = keyval
    key_defs[name_to_keycodes[keyname]][mod_values["ctrll"] + mod_values["alt"]] = f"Meta_{keyval}"


#for keydef in key_defs.values():
#    symlayer_symbol = keydef[mod_values["altgr"]]
#    if symlayer_symbol.lower() == symlayer_symbol:
#        keydef[mod_values["altgr"] + mod_values["control"]] = f"Control_{symlayer_symbol}"
#        keydef[mod_values["altgr"] + mod_values["control"] + mod_values["shift"]] = f"Control_{symlayer_symbol}"
#        keydef[mod_values["altgr"] + mod_values["control"] + mod_values["alt"]] = f"Meta_Control_{symlayer_symbol}"
#        keydef[mod_values["altgr"] + mod_values["control"] + mod_values["alt"] + mod_values["shift"]] = f"Meta_Control_{symlayer_symbol}"


for i in range(0, 10):
    keyname = f"KEY_{i}"
    keydef = key_defs[name_to_keycodes[keyname]]
    for i in range(1, 128):
        keydef[i] = keydef[0]


def hdr(text):
    print("#==========================================================================")
    print("#", text)
    print("#==========================================================================")
    print()


def get_single_symbol_map(keysym):
    if keysym in string.ascii_letters:
        symbols = []
        for i in range(128):
            mods = modlist(i)
            if 'control' in mods and 'alt' in mods:
                symbols.append(f"Meta_Control_{keysym.lower()}")
                continue
            if 'control' in mods:
                symbols.append(f"Control_{keysym.lower()}")
                continue
            newsym = keysym.swapcase() if "shift" in mods else keysym
            if "alt" in mods:
                symbols.append(f"Meta_{newsym}")
                continue
            symbols.append(newsym)
        return symbols
    return [keysym] * 128


def unicode_data(keysym):
    if not keysym.startswith('U+'):
        return ''
    as_str = chr(int(keysym[2:], base=16))
    return f'# {as_str} ({unicodedata.name(as_str)})'


def print_keycode_line(keycode, keysym, mods=()):
    mods_expn = ' '.join(mods)
    shift = 'shift' if 'shift' in mods else '     '
    altgr = 'altgr' if 'altgr' in mods else '     '
    control = 'control' if 'control' in mods else '       '
    alt = 'alt' if 'alt' in mods else '   '
    ctrll = 'ctrll' if 'ctrll' in mods else '     '
    udata = unicode_data(keysym)
    if 'GREEK' in udata:
        return
    print(f"{ctrll} {alt} {control} {altgr} {shift} keycode {keycode:>3} = {keysym:10} {udata}".rstrip())


def print_key(keycode, key_def):
    implicit_map = get_single_symbol_map(key_def[0])
    for i in range(0, 128):
        if key_def[i] in ('VoidSymbol', 'nul', 'Meta_nul'):
            key_def[i] = implicit_map[i]
    print_keycode_line(keycode, key_def[0])
    while implicit_map != key_def:
        for mod_idx in range(1, 128):
            need_symb = key_def[mod_idx]
            if need_symb == implicit_map[mod_idx]:
                continue
            mods = modlist(mod_idx)
            if (
                    len(mods) < 4
                    and 'shiftr' not in mods
                    and 'shiftl' not in mods
                    and set(mods) != {"ctrll", "shift"}
                    and set(mods) != {"control", "altgr"}
                    and set(mods) != {"control", "altgr", "shift"}
                    and set(mods) != {"alt", "control", "altgr"}
                    and set(mods) != {"ctrll", "control", "altgr"}
            ):
                print_keycode_line(keycode, need_symb, mods=mods)
            implicit_map[mod_idx] = need_symb


print("# 3L Keyboard Layout")
print("# ==================")
print("# 3L is a derivative of the Neo keyboard layout, designed for typing")
print("# English text.  For more information, visit:")
print("# https://github.com/jackrosenthal/threelayout")
print("#")
print("# In this implementation, the Sym layer (Mod3 in Neo) is implemented under")
print("# AltGr, and the Cur layer (Mod4 in Neo) is implemented under CtrlL.")
print()


prelude.append('include "linux-keys-bare"')
hdr("Prelude")
for line in prelude:
    print(line)
print()


for row_name, row_key_names in rows:
    hdr(row_name)
    for key_name in row_key_names:
        print("# {}".format(key_name))
        keycode = name_to_keycodes[key_name]
        print_key(keycode, key_defs[keycode])
        print()
