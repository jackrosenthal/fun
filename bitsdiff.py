#!/usr/bin/env python3

import pathlib
import click

@click.command()
@click.argument("a", type=pathlib.Path)
@click.argument("b", type=pathlib.Path)
def main(a, b):
    a_bytes = a.read_bytes()
    b_bytes = b.read_bytes()

    bitstotal = 0
    bitsdiff = 0

    for a_by, b_by in zip(a_bytes, b_bytes):
        xor = a_by ^ b_by
        bitsdiff += xor.bit_count()
        bitstotal += 8

    print(f"{bitsdiff}/{bitstotal} bits differ ({bitsdiff / bitstotal * 100}%)")


if __name__ == '__main__':
    main()
