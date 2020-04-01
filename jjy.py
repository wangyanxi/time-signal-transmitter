#! /usr/bin/env python3

from datetime import datetime, timezone, timedelta
import sys
import signal
import time
import argparse
from ad9833 import AD9833

jjy_frequency = int(60 * 1000)

japan_timezone = timezone(timedelta(hours=9))

wave = AD9833()


def bcd_code(n, length):
    bin_str = format(n, '0' + str(length) + 'b')
    return [int(x) for x in bin_str]


def get_parity(codes):
    return sum(codes) % 2


def jjy_code(now):
    # http://jjy.jp/jjy/trans/index-e.html
    # http://jjy.jp/jjy/trans/timecode1-e.html

    assert now.second == 0

    codes = []

    codes.append(2)  # marker

    # minute
    minute_code = bcd_code(now.minute // 10, 3) + bcd_code(now.minute % 10, 4)
    codes.extend(minute_code[0:3])
    codes.append(0)
    codes.extend(minute_code[3:])

    codes.append(2)  # P1
    codes.extend([0, 0])

    # hour
    hour_code = bcd_code(now.hour // 10, 2) + bcd_code(now.hour % 10, 4)
    codes.extend(hour_code[0:2])
    codes.append(0)
    codes.extend(hour_code[2:])

    codes.append(2)  # P2
    codes.extend([0, 0])

    # day
    day = now.timetuple().tm_yday
    codes.extend(bcd_code(day // 100, 2))
    codes.append(0)
    codes.extend(bcd_code(day % 100 // 10, 4))
    codes.append(2)  # P3
    codes.extend(bcd_code(day % 10, 4))

    codes.extend([0, 0])

    # parity
    pa1 = get_parity(hour_code)
    pa2 = get_parity(minute_code)
    codes.extend([pa1, pa2])

    # Spare
    # These spare bits are reserved for future additions of items to be contained within the time code
    su1 = 0
    su2 = 0
    p4 = 2
    codes.extend([su1, p4, su2])

    # year
    codes.extend(bcd_code(now.year % 100 // 10, 4))
    codes.extend(bcd_code(now.year % 100 % 10, 4))

    codes.append(2)  # P5

    # week
    # 0 = sunday, 1 = monday, 6 = Saturday
    # date.isoweekday() Monday is 1 and Sunday is 7.
    codes.extend(bcd_code(now.isoweekday() % 7, 3))

    # Leap
    # The leap second is inserted immediately before 9:00 (Japan standard time) of the 1st day
    # of the month that is to contain the leap second.
    # Leap second information is continuously transmitted from 9:00 on day 2 of the previous month
    # to 8:59 on day 1 of the relevant month.
    ls1 = 0
    ls2 = 0
    codes.extend([ls1, ls2])

    # ss
    codes.extend([0, 0, 0, 0])

    # The position marker P0 normally corresponds to the start of the 59th second (for non-leap seconds).
    # However, for a positive leap second (insertion of a second), P0 corresponds to the start of the 60th
    # second (in this case, the 59th second is represented by a binary 0). For a negative leap second (removal
    # of a second), P0 corresponds to the start of the 58th second.
    codes.append(2)  # P0

    return codes


def broadcast_time():

    now = datetime.now(tz=japan_timezone)
    print('--- --- ---', now)

    codes = jjy_code(now)

    pulse_width_arr = [{
        0: 0.8,
        1: 0.5,
        2: 0.2
    }[code] for code in codes]

    for pluse_with in pulse_width_arr:

        wave.set_frequency(jjy_frequency)
        time.sleep(pluse_with)

        wave.set_frequency(0)
        now = datetime.now(tz=japan_timezone)
        time.sleep(1 - now.microsecond / 1e6)


def main():
    wave.set_frequency(0)

    now = datetime.now(tz=japan_timezone)

    time.sleep(60 - now.second - now.microsecond / 1e6)

    while True:
        broadcast_time()


def sys_signal_handler(sig, frame):
    wave.close()

    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sys_signal_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--frequency',
                        default=60,
                        type=int,
                        choices=[60, 40],
                        help='signal frequency in kHz (default: 60 kHz)')

    args = parser.parse_args()
    jjy_frequency = args.frequency * 1000

    main()

    # d = datetime(2004, 4, 1, hour=17, minute=25, second=0, tzinfo=japan_timezone)

    # code_time = {
    #     0: 0.8,
    #     1: 0.5,
    #     2: 0.2
    # }

    # expect = [2, 0, 1, 0, 0, 0, 1, 0, 1, 2, 0, 0, 0, 1, 0, 0, 1, 1, 1, 2, 0, 0, 0, 0, 0, 1, 0, 0, 1,
    # 2, 0, 0, 1, 0, 0, 0, 0, 1, 0, 2, 0, 0, 0, 0, 0, 0, 1, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2]

    # print(jjy_code(d))
    # print(expect)
    # print(jjy_code(d) == expect)



