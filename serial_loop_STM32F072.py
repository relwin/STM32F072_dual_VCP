"""
serial_loop_STM32F072.py

python 3.8
serial 3.5
usage: app COM1 COM2   (use port numbers assigned)

Testing dual VCP STM32F072-DISCO board project.
The F072 is a USB device with 2 virtual com ports.
The test FW stm32f0_dualvcp.ioc creates 2 Fullspeed VCPs, and cross connects them.
USB speed settings aren't really implemented in this FW, so run at max 12M.
FS USB packets are 1..64 bytes.
Let's test data thru-put back and forth.

- can't send packets >64 w/ this test FW
- sending to both ports quickly may stall a port (Red LED on bd indicates a "USB busy" condition)

"""
import threading
import queue
import os
import time
import sys
import serial  # 3.5
import random

packet_size = 64  # experiment w/different sizes


# Init USB serial ports 12000000, baud rate settings not really used on FW
def serial_init(com_port):
    try:
        ser = serial.Serial(com_port, baudrate=12000000, timeout=None)
        for d in range(0, 2):
            time.sleep(0.25)  # wait for USB drain
            ser.reset_input_buffer()  # in case frame data in the pipe
            ser.reset_output_buffer()
        return ser

    except serial.SerialException:
        print("SerialException: Can't Open", com_port)
        return None


# send to STM's COM port
def serial_write(ser, packet):
    ser.write(packet)
    ser.flush()  # works better w/this!


class SerialReader(object):
    """
    from Miniterm Terminal application.
    Copy blksize data bytes from serial port to Queue q
    """

    def __init__(self, serial_instance, q, blksize):
        self.serial = serial_instance
        self.alive = None
        self._reader_alive = None
        self.receiver_thread = None
        self.q = q
        self.blksize = blksize

    def _start_reader(self):
        """Start reader thread"""
        self._reader_alive = True
        self.receiver_thread = threading.Thread(target=self.reader, name='rx')
        self.receiver_thread.daemon = True
        self.receiver_thread.start()

    def _stop_reader(self):
        """Stop reader thread only, wait for clean exit of thread"""
        self._reader_alive = False
        self.receiver_thread.join()

    def start(self):
        """start worker threads"""
        self.alive = True
        self._start_reader()

    def stop(self):
        """set flag to stop worker threads"""
        self.alive = False
        self._stop_reader()

    def join(self, transmit_only=False):
        """wait for worker threads to terminate"""
        self.receiver_thread.join()

    def close(self):
        self.serial.close()

    def reader(self):
        """loop and queue serial data frames"""
        try:
            while self.alive and self._reader_alive:
                data = self.serial.read(self.blksize)
                self.q.put(data)

        except serial.SerialException:
            self.alive = False
            raise  # XXX handle instead of re-raise

    #===============================================


# usage: app COM1 COM2
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Missing COM ports")
        exit(-2)
    print("pyserial ver:", serial.__version__)
    ser1 = serial_init(sys.argv[1])
    if ser1 is None:
        exit(-1)  # many reasons to not connect
    ser2 = serial_init(sys.argv[2])
    if ser2 is None:
        exit(-1)  # many reasons to not connect

    print("Using COM Port:", ser1.name)
    print("Using COM Port:", ser2.name)

    serialQueue1 = queue.Queue(1024)  # input data Q
    serialQueue2 = queue.Queue(1024)
    sr1 = SerialReader(ser1, serialQueue1, packet_size)  # 1..64 works
    sr2 = SerialReader(ser2, serialQueue2, packet_size)
    # initial sync
    sr1.start()
    sr2.start()
    maxqsz = 0
    q1_data_ctr = 0
    q2_data_ctr = 0
    b1 = bytearray(os.urandom(packet_size))  # limit to 64
    b2 = bytearray(os.urandom(packet_size))
    #step thru these lines when debugging FW
    #serial_write(ser1, b1)
    serial_write(ser2, b2)
    if serialQueue2.qsize() > 0:
        print('rec2', serialQueue2.qsize(), 'bytes')
    if serialQueue1.qsize() > 0:
        print('rec1', serialQueue1.qsize(), 'bytes')

    dt = time.time() + 1
    ds = time.time()
    dir = True
    cmp1_bad_ctr = 0
    cmp2_bad_ctr = 0

    while True:
        # loopback data
        if serialQueue1.qsize() > 0:
            q1_data_ctr += 1  # serialQueue1.qsize(), not reliable
            q1_data = serialQueue1.get()
            if q1_data != b2:
                print('q1 bad!')
                cmp1_bad_ctr += 1
            # print('rec1[', q1_data_ctr, ']', q1_data)

        if serialQueue2.qsize() > 0:
            q2_data_ctr += 1
            q2_data = serialQueue2.get()
            if q2_data != b1:
                print('q2 bad!')
                cmp2_bad_ctr += 1
            # print('rec2[', q2_data_ctr, ']', q2_data)

        if time.time() > dt:
            dt = time.time() + 0.001  # needs a small delay or busy error LED
            if dir:
                b1 = bytearray(os.urandom(packet_size))
                serial_write(ser1, b1)
            else:
                b2 = bytearray(os.urandom(packet_size))  # gen new
                serial_write(ser2, b2)
            dir = not dir
            time.sleep(0.00001)  # pause to let new packet propagate

        if time.time() > ds:
            ds = time.time() + 5
            print('bytes: rec1:', q1_data_ctr, 'bad1:', cmp1_bad_ctr, ' rec2:', q2_data_ctr, 'bad2:', cmp2_bad_ctr)
