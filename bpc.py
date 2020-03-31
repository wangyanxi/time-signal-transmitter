#! /usr/bin/env python3

import sys
import signal
import datetime
import time
from ad9833 import AD9833


bpc_frequency = int(68.5 * 1000)


wave = AD9833()


def int_to_base(number, base):
    if number == 0:
        return [0]
    digits = []
    while number:
        digits.append(int(number % base))
        number //= base
    return digits[::-1]


def int_to_bpc_base(number, length):
    arr = int_to_base(number, 4)
    if len(arr) < length:
        arr = [0] * (length - len(arr)) + arr
    if len(arr) > length:
        arr = arr[-length:]
    return arr


def get_checksum(codes):
    b_arr = []
    for code in codes:
        b = bin(code)[2:]
        b_arr.extend(list(b))

    return b_arr.count('1') % 2


def bpc_code(now):
    codes = []

    if now.second == 1:
        p1 = 0
    elif now.second == 21:
        p1 = 1
    elif now.second == 41:
        p1 = 2
    else:
        raise Exception('wrong time')

    codes.append(p1)
    p2 = 0
    codes.append(p2)
    hour = now.hour
    is_afternoon = False
    if hour >= 12:
        hour -= 12
        is_afternoon = True
    codes.extend(int_to_bpc_base(hour, 2))
    codes.extend(int_to_bpc_base(now.minute, 3))
    codes.extend(int_to_bpc_base(now.isoweekday(), 2))

    p3 = get_checksum(codes) + (0b10 if is_afternoon else 0)
    codes.append(p3)

    codes.extend(int_to_bpc_base(now.day, 3))
    codes.extend(int_to_bpc_base(now.month, 2))
    codes.extend(int_to_bpc_base(now.year % 100, 3))

    p4 = get_checksum(codes[-8:])
    codes.append(p4)

    return codes


def code_time(code):
    if code == 0:
        return 0.1
    elif code == 1:
        return 0.2
    elif code == 2:
        return 0.3
    elif code == 3:
        return 0.4
    else:
        raise Exception('unknown code')


def broadcast_time():

    now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8)))
    print('--- --- ---', now)

    codes = bpc_code(now.replace(second=now.second + 1))

    time.sleep(1 - now.microsecond / 1e6)

    for i in range(len(codes)):

        wave.set_frequency(0)
        time.sleep(code_time(codes[i]))

        wave.set_frequency(bpc_frequency)

        now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8)))
        time.sleep(1 - now.microsecond / 1e6)


def main():

    wave.set_frequency(bpc_frequency)

    now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8)))
    second = now.second
    while second >= 20:
        second -= 20

    time.sleep(20 - second - now.microsecond / 1e6)

    while True:
        broadcast_time()


def sys_signal_handler(sig, frame):
    wave.close()

    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sys_signal_handler)
    main()

    # d = datetime.datetime(2004, 3, 9, hour=9, minute=15, second=1)
    # codes = bpc_code(d)
    # expect = [0, 0, 2, 1, 0, 3, 3, 0, 2, 1, 0, 2, 1, 0, 3, 0, 1, 0, 1]
    # print(codes == expect)

    # d = datetime.datetime(2010, 7, 2, hour=14, minute=38, second=41)
    # codes = bpc_code(d)
    # expect = [2, 0, 0, 2, 2, 1, 2, 1, 1, 3, 0, 0, 2, 1, 3, 0, 2, 2, 0]
    # print(codes == expect)



