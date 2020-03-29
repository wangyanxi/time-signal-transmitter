#! /usr/bin/env python3

import spidev
from functools import reduce

flag_b28 = 1 << 13
frequency_register_0 = 1 << 14
phase_register_0 = 1 << 14 | 1 << 15


# https://www.raspberrypi.org/documentation/hardware/raspberrypi/spi/README.md

# A hardware based implementation. This is only available when the SPI kernel module is loaded
# It can only use specific pins for SPI communication
# GPIO10=MOSI, physical pin 19
# GPIO9=MISO, physical pin 21
# GPIO11=SCLK, physical pin 23
# GPIO8=CE0, physical pin 24
# GPIO7=CE1, physical pin 26


class AD9833:

    def __init__(self, bus=0, device=0):

        spi = spidev.SpiDev()
        spi.open(bus, device)

        # Data is loaded into the device as a 16-bit word under the control of a serial clock input, SCLK.
        # Raspberry Pi do not support 16bits
        spi.bits_per_word = 8

        # The AD9833 is written to via a 3-wire serial interface
        # This serial interface operates at clock rates up to 40 MHz
        # https://www.raspberrypi.org/documentation/hardware/raspberrypi/spi/README.md
        spi.max_speed_hz = int(31.2e6)

        # Serial Clock Input. Data is clocked into the AD9833 on each falling edge of SCLK.
        # SCK idles high between write operations (CPOL = 1)
        # Data is valid on the SCK falling edge (CPHA = 0)
        # SPI mode as two bit pattern of clock polarity and phase [CPOL|CPHA], min: 0b00 = 0, max: 0b11 = 3
        spi.mode = 0b10

        flag_reset = 1 << 8

        codes = [flag_b28 | flag_reset,
                 frequency_register_0,
                 frequency_register_0,
                 phase_register_0,
                 flag_b28]

        self._spi = spi

        codes = reduce(lambda l1, l2: l1 + l2, [[code >> 8, code & 0xff] for code in codes])
        self._spi.writebytes(codes)

    def set_frequency(self, frequency):

        frequency_reg = round(frequency * (2 ** 28) / 25e6)

        reg_low = frequency_reg & 0x3fff
        reg_high = (frequency_reg >> 14) & 0x3fff

        codes = [flag_b28,
                 frequency_register_0 | reg_low,
                 frequency_register_0 | reg_high]

        codes = reduce(lambda l1, l2: l1 + l2, [[code >> 8, code & 0xff] for code in codes])
        self._spi.writebytes(codes)

    def close(self):

        self._spi.close()









