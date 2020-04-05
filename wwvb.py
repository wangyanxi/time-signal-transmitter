#! /usr/bin/env python3

from datetime import datetime, timezone, timedelta
import sys
import signal
import time
import calendar
from ad9833 import AD9833

wwvb_frequency = int(60 * 1000)

wave = AD9833()


def bcd_code(n, length):
    bin_str = format(n, '0' + str(length) + 'b')
    return [int(x) for x in bin_str]


def wwvb_code(now):

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

    # TODO: DUT1
    codes.extend([0, 1, 0])

    codes.append(2)  # P4

    # DUT1 value
    codes.extend(bcd_code(0, 4))

    codes.append(0)

    # year
    codes.extend(bcd_code(now.year % 100 // 10, 4))
    codes.append(2)  # marker
    codes.extend(bcd_code(now.year % 100 % 10, 4))

    codes.append(0)  # unused

    codes.append(int(calendar.isleap(now.year)))  # leap year
    # TODO: leap second
    codes.append(0)

    # TODO: DST
    # codes.extend([0, 0])
    codes.extend([1, 1])

    codes.append(2)  # marker

    return codes


def broadcast_time():

    now = datetime.now(tz=timezone.utc)
    print('--- --- ---', now)

    codes = wwvb_code(now)

    # The WWVB 60 kHz carrier, which has a normal ERP of 70 kW,
    # is reduced in power at the start of each UTC second by 17 dB (to 1.4 kW ERP).
    # It is restored to full power some time during the second.
    # The duration of the reduced power encodes one of three symbols:

    # If power is reduced for one-fifth of a second (0.2 s), this is a data bit with value zero.
    # If power is reduced for one-half of a second (0.5 s), this is a data bit with value one.
    # If power is reduced for four-fifths of a second (0.8 s), this is a special non-data "marker," used for framing.

    pulse_width_arr = [{
        0: 0.2,
        1: 0.5,
        2: 0.8
    }[code] for code in codes]

    for pluse_with in pulse_width_arr:

        wave.set_frequency(0)
        time.sleep(pluse_with)

        wave.set_frequency(wwvb_frequency)
        now = datetime.now(tz=timezone.utc)
        time.sleep(1 - now.microsecond / 1e6)


def main():
    wave.set_frequency(0)

    # WWVB broadcasts the time in Coordinated Universal Time (UTC)
    now = datetime.now(tz=timezone.utc)

    time.sleep(60 - now.second - now.microsecond / 1e6)

    while True:
        broadcast_time()


def sys_signal_handler(sig, frame):
    wave.close()

    sys.exit(0)


if __name__ == '__main__':

    # https://www.nist.gov/pml/time-and-frequency-division/radio-stations/wwvb/wwvb-time-code-format

    signal.signal(signal.SIGINT, sys_signal_handler)
    main()



