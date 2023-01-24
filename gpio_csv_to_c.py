#!/usr/bin/env python3

import csv
import dataclasses
import enum
import sys


class Direction(enum.Enum):
    OUTPUT = 0
    INPUT = 1

class Function(enum.Enum):
    GPIO = 0
    NATIVE = 1

class Level(enum.Enum):
    LOW = 0
    HIGH = 1


@dataclasses.dataclass
class GPIO:
    num: int
    nf: str
    net: str
    direction: Direction
    function: Function
    level: Level


input()
gpios = []
reader = csv.reader(sys.stdin)
for row in reader:
    num = int(row[0])
    nf = row[2]
    net = row[3]
    direction = Direction[row[4]]
    function = Function[row[5]]
    level = Level[row[6]]
    gpios.append(GPIO(num, nf, net, direction, function, level))

sets = [range(0, 32), range(32, 64), range(64, 76)]

print("/* SPDX-License-Identifier: GPL-2.0-only */")
print()
print("#include <southbridge/intel/common/gpio.h>")


for s_idx, s_rng in enumerate(sets):
    print()
    print(f"static const struct pch_gpio_set{s_idx+1} pch_gpio_set{s_idx+1}_mode = {{")
    for gpio in gpios:
        if gpio.num not in s_rng:
            continue
        print(f"\t.gpio{gpio.num:<2} = GPIO_MODE_{gpio.function.name + ',':<7} // Net: {gpio.net + ',':<19} NF: {gpio.nf}")
    print("};")

    print()
    print(f"static const struct pch_gpio_set{s_idx+1} pch_gpio_set{s_idx+1}_direction = {{")
    for gpio in gpios:
        if gpio.num not in s_rng:
            continue
        print(f"\t.gpio{gpio.num:<2} = GPIO_DIR_{gpio.direction.name},")
    print("};")

    print()
    print(f"static const struct pch_gpio_set{s_idx+1} pch_gpio_set{s_idx+1}_level = {{")
    for gpio in gpios:
        if gpio.num not in s_rng:
            continue
        print(f"\t.gpio{gpio.num:<2} = GPIO_LEVEL_{gpio.level.name},")
    print("};")

print()
print("const struct pch_gpio_map mainboard_gpio_map = {")
for s_idx in range(len(sets)):
    print(f"\t.set{s_idx + 1} = {{")
    for table in ("mode", "direction", "level"):
        xtab = "\t"
        if table == "direction":
            xtab = ""
        print(f"\t\t.{table}{xtab}\t= &pch_gpio_set{s_idx+1}_{table},")
    print("\t},")
print("};")
