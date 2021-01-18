#!/usr/bin/env python3

import enum
import random
import subprocess
import sys


class LineState(enum.Enum):
    RINGING = 0
    PROGRESS = 1
    ANSWER = 2
    HANGUP = 3


class AGIState:
    def __init__(self, digits='', dial_early=True,
                 initial_state=LineState.RINGING):
        self.dial_early = dial_early
        self.digits = list(reversed(digits))
        self.line_state = initial_state

    def process_command(self, command, *args):
        if command == 'ANSWER':
            assert self.line_state is not LineState.HANGUP
            self.line_state = LineState.ANSWER
            return 200, 0
        if command == 'HANGUP':
            assert self.line_state is not LineState.HANGUP
            self.line_state = LineState.HANGUP
            return 200, 0
        if command == 'STREAM':
            assert args[0] == 'FILE'
            assert self.line_state == LineState.ANSWER
            filename = args[1]
            interrupt_digits = '""'
            if len(args) == 3:
                interrupt_digits = args[2]
            if (self.digits and self.dial_early and interrupt_digits != '""' and
                    self.digits[-1] in interrupt_digits):
                return 200, ord(self.digits.pop())
            return 200, 0
        if command == 'WAIT':
            assert args[0] == 'FOR'
            assert args[1] == 'DIGIT'
            timeout = -1
            if len(args) == 3:
                timeout = int(args[2])
            if not self.digits:
                if timeout > 0:
                    return 200, 0
                return 200, -1
            return 200, ord(self.digits.pop())
        if command == 'RECORD':
            assert args[0] == 'FILE'
            filename = args[1]
            assert args[2] == 'sln16'
            with open(filename, 'w') as f:
                pass
            return 200, 0
        assert False


def send_agivars(agivars, out_file):
    for var, value in agivars.items():
        line = "{}: {}".format(var, value)
        print("<=", line)
        print(line, file=out_file)
    print("-----")
    print(file=out_file)


def run_test(state):
    agifile = sys.argv[1]

    proc = subprocess.Popen([agifile],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            encoding='utf-8')

    send_agivars({'agi_tester': True}, proc.stdin)
    proc.stdin.flush()

    give_5_to_finish = False

    while True:
        if give_5_to_finish:
            proc.communicate(timeout=5)
            assert state.line_state == LineState.HANGUP
            assert proc.returncode == 0
            return
        line = proc.stdout.readline().strip()
        cmd = line.split()
        print('=>', *cmd)
        if cmd[0] == 'HANGUP':
            give_5_to_finish = True
        status, result = state.process_command(*cmd)
        response = '{} result={}'.format(status, result)
        print('<=', response)
        print(response, file=proc.stdin)
        proc.stdin.flush()


def main():
    run_test(AGIState(digits='199683069703677115'))


if __name__ == '__main__':
    main()
