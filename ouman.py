#!/usr/bin/env python2

import serial
import struct


STX = '\x02'
ACK = '\x06'


def calc_crc(data):
    # crc is just an 8-bit sum
    data = struct.unpack('B' * len(data), data)
    crc = struct.pack('B', sum(data) & 0xff)
    return crc


def fmt_cmd(cmd):
    cmd = struct.pack('!h', cmd)  # commands are 16 bit
    header = '\x81' + chr(len(cmd))
    crc = calc_crc(header + cmd)
    return STX + header + cmd + crc


def readOuman(cmd):
    buf = fmt_cmd(cmd)
    serio.write(buf)
    serio.flush()

    # First two bytes should be STX+ACK
    stx = serio.read()
    if stx != STX:
        return None
    ack = serio.read()
    if ack != ACK:
        print "serio failed: %s" % (ack)
        return None

    datalen = serio.read()
    try:
        n, = struct.unpack('B', datalen)
    except:
        print "Getting data length failed: datalen = %s" % (datalen)
        return None

    data = serio.read(n)
    checksum = serio.read()
    crc = calc_crc(ack + datalen + data)
    if not checksum or crc != checksum:
        print "checksum failed: %s != %s" % (crc, checksum)
        return None

    cmd2, val = struct.unpack('!hh', data)
    if cmd2 != cmd:
        print "command failed: %s != %s" % (cmd2, cmd)
        return None

    return val


if __name__ == '__main__':
    global serio
    serio = serial.Serial('/dev/ttyUSB0', 4800, timeout=1)
    print readOuman(18)
    serio.close()
