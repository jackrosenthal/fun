#!/usr/bin/env python3

import datetime
import enum
import os
import pathlib
import regex
import sys
import tempfile

import pocketsphinx


class AsteriskChannelError(Exception):
    pass


class DigitPressTimeout(Exception):
    pass


class MaxRetriesExceeded(Exception):
    pass


class TooYoungToVax(Exception):
    pass


class SkipMessage(Exception):
    pass


def get_agivars():
    agivars = {}
    while True:
        line = input()
        if not line:
            return agivars
        var, _, value = line.partition(': ')
        agivars[var] = value


def agi(command, *args):
    print(command, *args)
    response = input()
    response_code, _, rest = response.partition(' result=')
    if response_code == '200':
        rv, _, rest = rest.partition(' ')
        return int(rv), rest
    raise AsteriskChannelError(response)


def stream_file(filename, escape_digits='""'):
    rv, _ = agi('STREAM FILE', filename, escape_digits)
    if rv == -1:
        raise AsteriskChannelError('STREAM FILE returned -1')
    if rv == 0:
        return None
    return chr(rv)


def stream_file_skippable(filename, skipchr='#'):
    rv = stream_file(filename, skipchr)
    if rv == skipchr:
        raise SkipMessage()
    return rv


def wait_for_digit(timeout=-1):
    rv, _ = agi('WAIT FOR DIGIT', timeout)
    if rv == -1:
        raise AsteriskChannelError('STREAM FILE returned -1')
    if rv == 0:
        raise DigitPressTimeout()
    return chr(rv)


def stream_file_read_digits(filename, re=regex.compile(r'\d'), tries=3,
                            digit_timeout=30 * 1000,
                            try_again_filename='inval'):
    if tries <= 0:
        raise MaxRetriesExceeded()

    # Figure out escape digits
    escape_digits = ''
    for digit in '123456789*0#':
        if re.fullmatch(digit, partial=True):
            escape_digits += digit

    string_read = ''
    char_read = stream_file(filename, escape_digits=escape_digits)
    if char_read:
        string_read += char_read

    def try_again():
        stream_file(try_again_filename)
        return stream_file_read_digits(
            filename, re=re, tries=tries - 1, digit_timeout=digit_timeout,
            try_again_filename=try_again_filename)

    while True:
        if re.fullmatch(string_read):
            return string_read
        if not re.fullmatch(string_read, partial=True):
            return try_again()
        try:
            string_read += wait_for_digit(digit_timeout)
        except DigitPressTimeout:
            return try_again()


def get_dob():
    stream_file('vaxline_dob_intro')

    year_iput = stream_file_read_digits(
        'vaxline_dob_year',
        re=regex.compile('19\d\d|20[01]\d|202[01]'))
    year = int(year_iput)
    if year >= 2006:
        raise TooYoungToVax()

    stream_file('vaxline_thank_you')
    month_iput = stream_file_read_digits(
        'vaxline_dob_month',
        re=regex.compile('[0123456789*0#]'))
    stream_file('vaxline_thank_you')

    month = {
        '1': 1,
        '2': 2,
        '3': 3,
        '4': 4,
        '5': 5,
        '6': 6,
        '7': 7,
        '8': 8,
        '9': 9,
        '*': 10,
        '0': 11,
        '#': 12,
    }[month_iput]

    re_28_days = regex.compile(r'0[1-9]|1[0-9]|2[0-8]|[3-9]')
    re_29_days = regex.compile(r'0[1-9]|[12][0-9]|[3-9]')
    re_30_days = regex.compile(r'0[1-9]|[12][0-9]|30|[4-9]')
    re_31_days = regex.compile(r'0[1-9]|[12][0-9]|3[01]|[4-9]')

    month_days_re = {
        1: re_31_days,
        2: re_28_days,
        3: re_31_days,
        4: re_30_days,
        5: re_31_days,
        6: re_30_days,
        7: re_31_days,
        8: re_31_days,
        9: re_30_days,
        10: re_31_days,
        11: re_30_days,
        12: re_31_days,
    }

    if year % 4 == 0:
        month_days_re[2] = re_29_days

    day_iput = stream_file_read_digits(
        'vaxline_dob_day',
        re=month_days_re[month])

    return datetime.date(year, month, int(day_iput))


def age_in_years(dob):
    today = datetime.date.today()
    years = today.year - dob.year
    if today.month < dob.month or (today.month == dob.month
                                   and today.day < dob.day):
        years -= 1
    return years


class Phase(enum.Enum):
    PHASE_1A_OR_1B_ABOVE_DOTTED_LINE = 1
    PHASE_1B_BELOW_DOTTED_LINE = 2
    PHASE_2 = 3
    PHASE_3 = 4


def get_phase(dob):
    if age_in_years(dob) >= 70:
        return Phase.PHASE_1A_OR_1B_ABOVE_DOTTED_LINE

    digit_map = {
        '1': Phase.PHASE_1A_OR_1B_ABOVE_DOTTED_LINE,
        '2': Phase.PHASE_1B_BELOW_DOTTED_LINE,
        '3': Phase.PHASE_2,
        '4': Phase.PHASE_2,
        '5': Phase.PHASE_2,
    }

    stream_file('vaxline_phase_intro')

    if age_in_years(dob) >= 60:
        result = stream_file('vaxline_phase_msg1', escape_digits='123')
        if not result:
            result = stream_file('vaxline_phase_gt60_exit', escape_digits='123')
        if not result:
            try:
                result = wait_for_digit(30 * 1000)
            except DigitPressTimeout:
                result = '3'
        return digit_map.get(result, Phase.PHASE_2)

    result = stream_file('vaxline_phase_msg1', escape_digits='123456')
    if not result:
        result = stream_file('vaxline_phase_msg2', escape_digits='123456')
    if not result:
        try:
            result = wait_for_digit(30 * 1000)
        except DigitPressTimeout:
            result = '6'
    return digit_map.get(result, Phase.PHASE_3)


def handle_call():
    try:
        stream_file_skippable('vaxline_intro_1a')
        stream_file_skippable('vaxline_intro_1b')
        stream_file_skippable('vaxline_intro_1c')
        stream_file_skippable('vaxline_on_the_web')
    except SkipMessage:
        pass

    dob = get_dob()

    if age_in_years(dob) < 16:
        raise TooYoungToVax

    phase = get_phase(dob)

    phone_number = stream_file_read_digits(
        'vaxline_phone_number',
        re=regex.compile(
            r'1?([2-8]\d\d|9[0-8]\d)[2-9]\d{2}\d{4}'))
    if not phone_number.startswith('1'):
        phone_number = '1{}'.format(phone_number)

    stream_file('vaxline_name')

    with tempfile.NamedTemporaryFile(delete=False, suffix='.raw') as f:
        file_name = f.name

    agi('RECORD FILE', file_name, 'sln16', '""', 20 * 1000, 0, 1, 'S=5')

    return (dob, phase, phone_number, file_name)


def submit_form(dob, phase, phone_number, recording_file_name):
    dict_file_path = pathlib.Path(__file__).parent / 'names.dict'
    sphinx = pocketsphinx.Pocketsphinx(dict=str(dict_file_path), verbose=False)
    sphinx.decode(audio_file=recording_file_name)
    best_list = list(sphinx.best(1))
    if best_list:
        full_name = best_list[0][0].upper()
    else:
        full_name = '<unclear audio>'
    os.unlink(recording_file_name)

    with open('/tmp/result.txt', 'w') as f:
        print('DOB={!r}, PHASE={!r}, PHONE={!r}, NAME={!r}'.format(
            dob, phase, phone_number, full_name), file=f)


def main():
    get_agivars()
    agi('ANSWER')
    result = None
    try:
        result = handle_call()
    except MaxRetriesExceeded:
        pass
    except TooYoungToVax:
        stream_file('vaxline_too_young')
    finally:
        agi('HANGUP')

    if result:
        submit_form(*result)


if __name__ == '__main__':
    main()
