import serial
import struct


class Ouman(object):
    STX = '\x02'
    ACK = '\x06'

    def __init__(self, dev):
        self.serio = serial.Serial(dev, 4800, timeout=1)

    def close(self):
        self.serio.close()

    def read(self, cmd):
        buf = self._fmt_cmd(cmd)
        self.serio.write(buf)
        self.serio.flush()

        # First two bytes should be STX+ACK
        stx = self.serio.read()
        if stx != self.STX:
            return None
        ack = self.serio.read()
        if ack != self.ACK:
            print "serio failed: %s" % (ack)
            return None

        datalen = self.serio.read()
        try:
            n, = struct.unpack('B', datalen)
        except:
            print "Getting data length failed: datalen = %s" % (datalen)
            return None

        data = self.serio.read(n)
        checksum = self.serio.read()
        crc = self._calc_crc(ack + datalen + data)
        if not checksum or crc != checksum:
            print "checksum failed: %s != %s" % (crc, checksum)
            return None

        cmd2, val = struct.unpack('!hh', data)
        if cmd2 != cmd:
            print "command failed: %s != %s" % (cmd2, cmd)
            return None

        return val

    def _calc_crc(self, data):
        # crc is just an 8-bit sum
        data = struct.unpack('B' * len(data), data)
        crc = struct.pack('B', sum(data) & 0xff)
        return crc

    def _fmt_cmd(self, cmd):
        cmd = struct.pack('!h', cmd)  # commands are 16 bit
        header = '\x81' + chr(len(cmd))
        crc = self._calc_crc(header + cmd)
        return self.STX + header + cmd + crc
