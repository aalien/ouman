import logging
from logging import debug
from xml.etree import cElementTree
import serial
import struct


#logging.basicConfig(level=logging.DEBUG)


class MeasurePoint(object):
    def __init__(self, elem, parent):
        self.idx = int(elem.get('nvIndex'))
        self.mask = int(elem.get('mask', 0))
        self.name = elem.get('name', '')
        self.datastart = int(elem.get('dataStartIndex', 0))
        self.dataend = int(elem.get('dataEndIndex', 0))
        self.unit = elem.get('unit', '')
        self.divisor = int(elem.get('divisor', 1))
        self.__ouman = parent

    def read(self):
        return self.__ouman.read(self)


class Ouman(object):
    STX = b'\x02'
    ACK = b'\x06'

    def __init__(self, configfile):
        self.__serio = None
        self.__measurepoints = {}

        root = cElementTree.parse(configfile)
        for elem in root.iter('MeasurePoint'):
            mp = MeasurePoint(elem, self)
            self.__measurepoints[mp.idx, mp.mask] = mp

    def connect(self, dev, baudrate=4800, timeout=1):
        self.__serio = serial.Serial(dev, baudrate, timeout=timeout)
        self.__serio.reset_input_buffer()
        self.__serio.reset_output_buffer()

    def close(self):
        self.__serio.close()

    def measurepoint(self, idx, mask=0):
        return self.__measurepoints[idx, mask]

    def measurepoints(self):
        return self.__measurepoints.values()

    def read(self, measurepoint):
        value = self.__read(measurepoint.idx, measurepoint.datastart, measurepoint.dataend)
        try:
            if measurepoint.mask:
                return value & measurepoint.mask
            return value / measurepoint.divisor
        except TypeError:
            return None

    def __read(self, cmd, s, e):
        debug('reading id %i', cmd)
        buf = self.__fmt_cmd(cmd)
        debug('sending %s', buf)
        self.__serio.write(buf)
        self.__serio.flush()

        # First two bytes should be STX+ACK
        stx = self.__serio.read()
        if stx != self.STX:
            return None
        ack = self.__serio.read()
        if ack != self.ACK:
            debug('serio failed: %s', ack)
            return None

        datalen = self.__serio.read()
        try:
            n, = struct.unpack('B', datalen)
            debug('datalen = %i', n)
        except:
            debug('Getting data length failed: datalen = %i', datalen)
            return None

        data = self.__serio.read(n)
        checksum = self.__serio.read()
        crc = self.__calc_crc(ack + datalen + data)
        if not checksum or crc != checksum:
            debug('checksum failed: %s != %s', crc, checksum)
            return None

        debug('data = %s', repr(data))
        cmd_str, data = data[0:2], data[2:]
        cmd2, = struct.unpack('!h', cmd_str)
        if cmd2 != cmd:
            debug('command failed: %s != %s', cmd2, cmd)
            return None

        data = data[s:e + 1]
        value_len = e - s + 1
        unpack_fmt = {1: 'b', 2: '!h', 4: '!i'}[value_len]
        debug('unpacking %s with value_len = %i and unpack_fmt = %s', data, value_len, unpack_fmt)
        val, = struct.unpack(unpack_fmt, data)

        return val

    def __calc_crc(self, data):
        # crc is just an 8-bit sum
        data = struct.unpack('B' * len(data), data)
        crc = struct.pack('B', sum(data) & 0xff)
        return crc

    def __fmt_cmd(self, cmd):
        cmd = struct.pack('!h', cmd)  # commands are 16 bit
        header = b'\x81' + bytearray((len(cmd),))
        crc = self.__calc_crc(header + cmd)
        return self.STX + header + cmd + crc
