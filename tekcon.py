#!/usr/bin/env python3

"""Tektronix 4006-1 Serial Translator"""

import argparse
import os
import serial
import string
import subprocess
import time
import tty
import sys
import termios
import select


keyb_to_val = [
    2,
    127,
    63,
    126,
    31,
    125,
    62,
    124,
    15,
    123,
    61,
    122,
    30,
    121,
    60,
    120,
    7,
    119,
    59,
    118,
    29,
    117,
    58,
    116,
    14,
    115,
    57,
    114,
    28,
    113,
    56,
    112,
    3,
    111,
    55,
    110,
    27,
    109,
    54,
    108,
    13,
    107,
    53,
    106,
    26,
    105,
    52,
    104,
    6,
    103,
    51,
    102,
    25,
    101,
    50,
    100,
    12,
    99,
    49,
    98,
    24,
    97,
    48,
    96,
    1,
    95,
    47,
    94,
    23,
    93,
    46,
    92,
    11,
    91,
    45,
    90,
    22,
    89,
    44,
    88,
    5,
    87,
    43,
    86,
    21,
    85,
    42,
    84,
    10,
    83,
    41,
    82,
    20,
    81,
    40,
    80,
    0,
    79,
    39,
    78,
    19,
    77,
    38,
    76,
    9,
    75,
    37,
    74,
    18,
    73,
    36,
    72,
    4,
    71,
    35,
    70,
    17,
    69,
    34,
    68,
    8,
    67,
    33,
    66,
    16,
    65,
    32,
    64,
]

val_to_keyb = [None for _ in range(len(keyb_to_val))]
for i, c in enumerate(keyb_to_val):
    val_to_keyb[c] = i


class Console:
    def __init__(self, ser, echo=True):
        self.ser = ser
        self.echo = echo

    def clear(self):
        self.putch("\x1a\x0c")

    def graph_mode(self):
        self.putch("\x1d")

    def text_mode(self):
        self.putch("\x1f")

    def getch(self):
        data = self.ser.read(1)
        byte = data[0]
        if byte < len(val_to_keyb):
            ch = chr(val_to_keyb[byte])
            if ch == "\x7f":
                return "\x08"
            if ch == "\r":
                return "\r\n"
            return ch
        return None

    def putch(self, ch):
        if ch == "\x08":
            ch = "\x1d\x1f"
        if ch == "\n":
            ch = "\r\n"

        for c in ch:
            c_val = ord(c)
            if c_val >= 128:
                c_val = ord("?")
            new_byte = val_to_keyb[c_val]
            self.ser.write(bytes([new_byte]))
            time.sleep(0.01)

    def run(self, stdin, stdout):
        os.set_blocking(stdin.fileno(), False)
        self.clear()
        while True:
            rlist, _, _ = select.select([stdin, self.ser], [], [])
            if not self.ser.is_open or stdout.closed:
                return
            if self.ser in rlist:
                ch = self.getch()
                if ch is not None:
                    stdout.write(ch)
                    stdout.flush()
                    if self.echo:
                        for c in ch:
                            self.putch(c)

            data = stdin.read(4096)
            for ch in data:
                if stdin.isatty() and ch == "\r":
                    ch = "\n"
                self.putch(ch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-f", "--tty", default="/dev/ttyUSB0", help="Serial console to attach to"
    )
    parser.add_argument("-b", "--baud", default=4800, type=int, help="Baud rate")
    parser.add_argument("-c", "--command", help="Command to run on console")
    parser.add_argument(
        "-e",
        "--echo",
        action="store_true",
        default=True,
        help="Echo characters back to the terminal",
    )
    parser.add_argument(
        "--no-echo", action="store_false", dest="echo", help="Disable echo"
    )
    args = parser.parse_args()

    with serial.Serial(args.tty, args.baud) as ser:
        console = Console(ser, echo=args.echo)
        if args.command:
            env = dict(os.environ)
            env["TERM"] = "dumb"
            with subprocess.Popen(
                args.command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                encoding="utf-8",
                errors="replace",
            ) as proc:
                console.run(proc.stdout, proc.stdin)
        elif sys.stdin.isatty():
            old_attr = termios.tcgetattr(sys.stdin.fileno())
            try:
                tty.setraw(sys.stdin.fileno())
                console.run(sys.stdin, sys.stdout)
            finally:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_attr)
        else:
            console.run(sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
