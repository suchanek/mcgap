#
# Motor Control Software for the MIRA gap.
# Author: Gary Love, with help from Eric Suchanek
#

import tkinter as tk
from tkinter import *
from tkinter.filedialog   import askopenfilename
from tkinter.filedialog   import asksaveasfilename
from tkinter import ttk
import serial.tools.list_ports

import pymodbus.exceptions
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.exceptions import ModbusIOException as ModbusException
from pymodbus.exceptions import ConnectionException as ConnException

import simpleaudio as sa

from functools import partial
import serial
import usb.core
import sys
import os

import os.path as path
import pathlib

import logging
import copy
from time import sleep

FORMAT = ('%(asctime)-15s %(threadName)-15s '
          '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')

# http://www.simplymodbus.ca/exceptions.htm
ExceptionCodes = {1: 'Illegal Function', 2: 'Illegal Data Address',
                  3: 'Illegal Data Value', 4: 'Slave Device Failure', 5: 'Acknowledge',
                  6: 'Slave Device Busy', 7: 'Negative Acknowlege', 8: 'Memory Parity Error',
                  10: 'Gateway Path Unavailable', 11: 'Gateway Target Device Failed to respond'}

logging.basicConfig(format=FORMAT)
log = logging.getLogger()

# Define Global Variables
READERROR = -999 # returned when can't read a motor
ATLIMIT = -888

filemenu = 0

limitSet = "Show"
# i don't know if this is right but DISABLE is used and wasn't defined globally
DISABLE = 0
TEST = 0
DBG = 1
DBG2 = 0

# Location = [0, 0, 0, 0, 0] # array of current coordinates

#Reference = [0, 0, 0, 0, 0]
#Zero = [0, 3000, 0, 1000, 1000]
#Speed = [0, 100, 100, 10000, 10000]
#Resolution = [0, 1000, 1000, 100000, 100000]
#Lower = [0, 0, 0, 0, 0]
#Upper = [0, 8000, 1000, 125000, 125000]
#Offset = [0, 8000, 1000, 15000, 15000]

# Initialize arrays
e = [0, 0, 0, 0, 0, 0, 0, 0]
l = [0, 0, 0, 0, 0]
o = [0, 0, 0, 0, 0]
s = [0, 0, 0, 0, 0]
u = [0, 0, 0, 0, 0]
z = [0, 0, 0, 0, 0]
_run = []

e1 = e2 = ''
tab = 0
key = ''
val = 0
label = ''
jog1 = jog2 = jog3 = jog4 = []
tab1 = tab2 = tab3 = tab4 = []
tmp1 = tmp2 = tmp3 = tmp4 = []
pos1 = pos2 = pos3 = pos4 = []
page = ["page[0]", "page[1]", "page[2]", "page[3]", "page[4]"]

PATH = pathlib.Path(__file__).parent.joinpath("").resolve()
CONFIG_FILENAME = "GAPMC.ozs"
CONFIG_PATH = PATH.joinpath(CONFIG_FILENAME)
CONFIG_POSIX = CONFIG_PATH.as_posix()

DFLT_FILENAME = "GAPMC.dft"
DFLT_PATH = PATH.joinpath(DFLT_FILENAME)
DFLT_POSIX = DFLT_PATH.as_posix()

def play_sound(sound_file):
    wave_obj = sa.WaveObject.from_wave_file(sound_file)
    play_obj = wave_obj.play()
    play_obj.wait_done()
    return

def beep(repeat):
    while repeat:
        play_sound('ping.wav')
        repeat -= 1

def menu():
    """
    Create a pulldown file menu, and add it to the menu bar
    """
    global filemenu

    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Open User Settings", font='Ariel 13', command=F.readUser)
    filemenu.add_command(label="Save User Settings", font='Ariel 13', command=F.saveUser)
    #filemenu.add_command(label=limitSet + " Limits", font='Ariel 13', command=T.setLimits)
    #filemenu.add_command(label="Reset to Prev Tablets", font='Ariel 13', command=T.resetTab)
    filemenu.add_command(label="Reset to Orig Defaults", font='Ariel 13', command=F.readDflt)
    filemenu.add_command(label="Configure Motors", font='Ariel 13', command=F.getPassword)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", font='Ariel 13', command=main.quit)
    menubar.add_cascade(label="File", menu=filemenu)

def message(unit, _mflag, msg):
    global page

    if _mflag == 1:
        if DBG2:
            print(unit, "MESSAGE:", msg, ">", page[unit], "<")
        tk.Label(page[unit], font='Ariel 13', foreground="#000000", text=msg).place(x=100, y=10, width=350, height=25)

    else:
        if DBG2:
            print(unit, "MESSAGE:", msg, ">", page[unit], "<")
        tk.Label(page[unit], font='Ariel 13', foreground="#F0F0F0", text=msg).place(x=100, y=10, width=350, height=25)

def warn():
    warn2 = "No motor is available."
    warn3 = "Connect and turn on motors."
    temp = tk.Tk()
    temp.wm_title('WARNING')
    w = Canvas(temp, width=340, height=150)
    w.pack()
    w.create_text(170, 15, text='WARNING:', font='Ariel 13', fill="#FF0000")
    w.create_text(170, 45, text=warn2, font='Ariel 13')
    w.create_text(170, 75, text=warn3, font='Ariel 13')

    _positionRight = int(temp.winfo_screenwidth()/2 - temp.winfo_reqwidth()/1)
    _positionDown = int(temp.winfo_screenheight()/2 - temp.winfo_reqheight()/1)

    temp.geometry(f'+{_positionRight}+{_positionDown}')

    b = tk.Button(w, text='QUIT', font='Ariel 15', width=35, command=exit, anchor=S)
    b.configure(width=10, activebackground="#BBBBBB")
    w.create_window(120, 110, anchor=NW, window=b)
    b.place(x=120, y=110)
    temp.mainloop()
    sys.exit()
    return

def run():
    global nb

    if M1.available:
        page[1] = ttk.Frame(nb)
        B.tablet1()
        p1 = M1.readMotor()
        if p1 == READERROR:
            # put up a warning that M1 can't be read...
            print("Can't read unit ", M1.unit)
            msg = f"Motor {M1.unit} is not available"
            message(M1.unit, 1, msg)
        else:
            I.setEntry(1, p1)
            slidePos = T.getRadioButn(1, tab1)
            slide.set(slidePos)
    else:
        page[1] = ttk.Frame(nb)
        msg = f"Motor {M1.unit} is not available"
        message(M1.unit, 1, msg)

    if M2.available:
        page[2] = ttk.Frame(nb)
        B.tablet2()
        p2 = M2.readMotor()
        if p2 == READERROR:
            # put up a warning that M1 can't be read...
            print("Can't read unit ", M2.unit)
            msg = f"Motor {M2.unit} is not available"
            message(M2.unit, 1, msg)
        else:
            I.setEntry(2, p2)
            cmparPos = T.getRadioButn(2, tab2)
            source.set(cmparPos)
    else:
        page[2] = ttk.Frame(nb)
        msg = f"Motor {M2.unit} is not available"
        message(M2.unit, 1, msg)

    if M3.available:
        page[3] = ttk.Frame(nb)
        B.tablet3()
        p3 = M3.readMotor()
        if p3 == READERROR:
            # put up a warning that M1 can't be read...
            print("Can't read unit ", M3.unit)
            msg = f"Motor {M3.unit} is not available"
            message(M3.unit, 1, msg)
        else:
            I.setEntry(3, p3)
            grat1Pos = T.getRadioButn(3, tab3)
            grate1.set(grat1Pos)
    else:
        page[3] = ttk.Frame(nb)
        msg = f"Motor {M3.unit} is not available"
        message(M3.unit, 1, msg)

    if M4.available:
        page[4] = ttk.Frame(nb)
        B.tablet4()
        p4 = M4.readMotor()
        if p4 == READERROR:
            # put up a warning that M4 can't be read...
            print("Can't read unit ", M4.unit)
            msg = f"Motor {M4.unit} is not available"
            message(M4.unit, 1, msg)
        else:
            I.setEntry(4, p4)
            grat2Pos = T.getRadioButn(4, tab4)
            grate2.set(grat2Pos)
    else:
        page[4] = ttk.Frame(nb)
        msg = f"Motor {M4.unit} is not available"
        message(M4.unit, 1, msg)
    return

def updateTabs():
    """
    Forget all tabs and restore with new settings
    """
    global page

    nb.forget(page[1])
    nb.forget(page[2])
    nb.forget(page[3])
    nb.forget(page[4])
    page = ["page[0]", "page[1]", "page[2]", "page[3]", "page[4]"]
    # this is very dangerous since recursive call to run... -egs-
    run()
    return

class MotorControl:
    """
	This class contains motor attributes and methods
	"""

    def __init__(self, unit, port, speed, position, zero, lower, upper, resolution, reference, offset, gearBox):
        """
        :rtype: object
        """
        self.unit = unit
        self.port = port
        self.speed = speed
        self.position = position # current step position
        self.reference = reference
        self.zero = zero
        self.lower = lower
        self.upper = upper
        self.offset = offset
        self.stp = 1
        self.deg = 1
        # make the correct object, don't try to connect
        self.client = ModbusClient(method='rtu')
        self.target = 0 # targeted step location
        self.connected = False
        self.available = self.isAvailable()
        self.resolution = self.getGearing(gearBox)
        

    def isAvailable(self):
        """
		Returns true if Motor is available, False otherwise.

		:rtype: boolean
		:param none:
		:return: True if we can connect to the motor, false otherwise.
		"""
        ok = self.connectMotor()
        self.closeMotor()
        if ok:
            self.available = True
        else:
            self.available = False
        return self.available

    def checkLimits(self):
        """
        Check for closure of limit switches. Assumes the motor is connected properly
        Returns 1 if at limit, 0 if OK and READERROR if an exception is thrown.
        """
        lim1 = lim2 = lim3 = 0

        if TEST:
            return 0

        if isinstance(self.client, ModbusException):
            self.connected = False
            return READERROR

        # the original calls failed, can you check? -egs- 0x200, 0x400, 0x800
        read = self.client.read_holding_registers(0x007F, 1, unit=self.unit)

        if read.isError():
            print("!!! checkLimits: got modbus exception: ", ExceptionCodes.get(read.exception_code))
        else:
            lim1 = read.registers[0]

        read = self.client.read_holding_registers(0x007F, 1, unit=self.unit)
        if read.isError():
            print("!!! checkLimits: got modbus exception: ", ExceptionCodes.get(read.exception_code))
        else:
            lim2 = read.registers[0]

        read = self.client.read_holding_registers(0x007F, 1, unit=self.unit)
        if read.isError():
            print("!!! checkLimits: got modbus exception: ", ExceptionCodes.get(read.exception_code))
        else:
            lim3 = read.registers[0]

        # note that we are not actually getting limits properly yet, so i just return 0
        if lim1 or lim2 or lim3:
            self.stopMotor()
            return 0
        return 0

    def checkMotor(self):
        """
        Return true if the motor is connected and client is not a modbusioException,
        and true if we can read a register from the unit. Properly manages self.connected.
        Assumes motor is connected with self.connectMotor()
        """
        read = 0

        if TEST:
            self.connected = TRUE
            return True

        if isinstance(self.client, ModbusException):
            print("!!! checkMotor: Modbus ioexception for unit ", self.unit)
            self.connected = False
            return False
        # attempt to read a register - if we can't then we have a problem
        read = self.client.read_holding_registers(0x00D7, 1, unit=self.unit)
        if read.isError():
            print(f"!!! checkMotor: Modbus ioexception for unit {self.unit}, error {ExceptionCodes.get(read.exception_code)}")
            self.connected = False
        else:
            self.connected = True
        return self.connected

    def closeMotor(self):
        """
		Close connection to motor unit

		:rtype: object
		:param unit:
		:return:
		"""
        if TEST:
            self.connected = False
            self.client = 0
            return

        try:
            self.client.close()
            if DBG:
                print(f">>> closeMotor: Close for unit {self.unit} succeeded")
        except:
            print(f"!!! closeMotor: Can't close unit {self.unit}: exception thrown!")
        self.connected = False
        self.client = 0
        return

    def connectMotor(self):
        """
		Connect to motor unit

		:rtype: Boolean
		:return: True if success, False otherwise
		"""
        res = 0

        if TEST:
            self.client = ModbusClient(method='rtu', baudrate=9600)
            self.connected = True
            return True

        self.client = ModbusClient(method='rtu', port=self.port, retries=100, timeout=0.5,
                                   rtscts=True, parity='E', baudrate=9600, strict=False, stopbits=2,
                                   unit=self.unit)

        if isinstance(self.client, ConnException):
            print(f"!!! connectMotor: Connection error for unit {self.unit}")
            self.connected = False
            return False

        if DBG:
            print(f">>> connectMotor: Connecting to unit {self.unit}")

        res = self.client.connect()
        if res:
            self.connected = True
           
           # return True
        else:
            self.connected = False
            print(f"!!! connectMotor: Can't connect to unit {self.unit}")
            return False
        
        read = self.client.read_holding_registers(0x007F, 1, unit=self.unit)
        if read.isError():
            print(f"!!! connectMotor: Unit {self.unit} got modbus error: {read.message}")
            self.connected = False
            return False
        else:
            if DBG:
                print(f">>> connectMotor: Connected unit {self.unit}")
            self.connected = True
            return True


    def jogMotor(self, delta):
        """
        Adjust motor position by delta. Functions called within this routine
        that read/write to the motor should NOT call connectMotor() or closeMotor().

        :param: delta correction for new motor position
        :return: new position, or READERROR otherwise
        """
        global tk
        cp = READERROR

        if DBG:
            print(f">>> jogMotor Unit: {self.unit}, Delta: {delta}")

        if self.outOfRange(delta):
            if DBG:
                print(f"!!! jogMotor Unit: {self.unit}: Jog is out of range! Returning")
            return READERROR

        if TEST:
            self.position = self.position + int(delta)
            #Location[self.unit] = self.position
            I.setEntry(self.unit, self.position)
            T.setLabel(self.unit, self.position)
            T.setTmpArr(self.unit, self.position)
            return self.position

        cp = self.readMotor()
        jogPosition = int(delta) + cp
        self.target = jogPosition
        self.sendMotor(jogPosition)

        rp = self.readMotor()

        if self.unit == 1:
            slidePos = T.getRadioButn(1, tab1)
            slide.set(slidePos)
        if self.unit == 2:
            cmparPos = T.getRadioButn(2, tab2)
            source.set(cmparPos)
        if self.unit == 3:
            grat1Pos = T.getRadioButn(3, tab3)
            grate1.set(grat1Pos)
        if self.unit == 4:
            grat2Pos = T.getRadioButn(4, tab4)
            grate2.set(grat2Pos)
        
        I.setEntry(self.unit, rp)
        T.setLabel(self.unit, rp)
        T.setTmpArr(self.unit, rp)

        if DBG:
            print(f">>> JogHERE Unit: {self.unit} jogPosition = {rp}")
        if jogPosition != rp:
            if DBG:
                print(f"??? jogMotor jogPos {jogPosition}, rp: {rp}")
            return READERROR

        # all ok, return position
        return rp

    def outOfRange(self, delta):
        """
		Check if the desired delta position is within normal range

		:param: delta correction for new motor position
		:return: False if OK, True if out of range
		"""
        global tk
        res = True

        msg = f"{self.position} + {int(delta)} is Out of Range"

        if self.position + int(delta) < self.lower or self.position + int(delta) > self.upper:
            if DBG:
                print(f"!!! outOfRange: Unit: {self.unit} pos {self.position + int(delta)}")
            message(self.unit, 1, msg)
            #tk.Label(page[self.unit], font='Ariel 13', foreground="#000000", text=msg).place(x=50, y=240, width=350, height=25)
            res = True
        else:
            #tk.Label(page[self.unit], font='Ariel 13', foreground="#D4D0C8", text=msg).place(x=50, y=240, width=350, height=25)
            message(self.unit, 2, msg)
            res = False
        return res

    def chkAlrm(self):
        """
		Check the given object for alarm conditions.
		:return: alarm or READERROR otherwise. Assumes motor
        is connected and readable.
		"""

        read = READERROR
        alarm = 0

        if TEST:
            return 0

        if isinstance(self.client, ModbusException):
            return READERROR

        read = self.client.read_holding_registers(0x007F, 1, unit=self.unit)
        if read.isError():
            print(f"!!! checkAlrm: got modbus exception: {ExceptionCodes.get(read.exception_code)}")
            return READERROR
        else:
            alarm = read.registers[0] # returned 32 with normal operation
            read = self.client.read_holding_registers(0x0081, 1, unit=self.unit)
            if read.isError():
                print(f"!!! checkAlrm: got modbus exception: {ExceptionCodes.get(read.exception_code)}")
                return False
            else:
                alarm = read.registers[0]

        if TEST:
            alarm = 64
        return alarm

    def rstAlrm(self):
        """
		Reset the alarm for the object.
		:return: True if reset, False if unable to reset, or READERROR otherwise.
        Assumes the motor is connected and available.
		"""
        global TEST

        if isinstance(self.client, ModbusException):
            return False

        if TEST:
            return True

        # you can only write registers if the motor is available.
        self.client.write_register(0x7D, 0x80, unit=self.unit)
        self.client.write_register(0x7D, 0x0, unit=self.unit)
        return True

    def showAlarm(self, error):
        warn2 = f"Motor {self.unit} has an alarm: {error}"

        # NEED A DICTIONARY FOR NESSAGES
        if error == 99:
            warn4 = "Motor driver is unreachable. Check power."
        temp = tk.Tk()
        temp.wm_title('ALARM')
        w = Canvas(temp, width=340, height=150)
        w.pack()
        w.create_text(170, 15, text='ERROR:', font='Ariel 13', fill="#FF0000")
        w.create_text(170, 45, text=warn2, font='Ariel 13')
        w.create_text(170, 70, text="", font='Ariel 13')
        w.create_text(170, 95, text="", font='Ariel 13')

        _positionRight = int(temp.winfo_screenwidth()/2 - temp.winfo_reqwidth()/1)
        _positionDown = int(temp.winfo_screenheight()/2 - temp.winfo_reqheight()/2)

        temp.geometry(f"+{_positionRight}+{_positionDown}")

        b = tk.Button(w, text='Reset', font='Ariel 13', width=30, command=self.rstAlrm, anchor=S)
        b2 = tk.Button(w, text='Okay', font='Ariel 13', width=30, command=temp.destroy, anchor=S)
        b.configure(width=10, activebackground="#BBBBBB")
        b2.configure(width=10, activebackground="#BBBBBB")
        b.place(x=20, y=100)
        b2.place(x=180, y=100)
        beep(1)
        temp.mainloop()
        temp.destroy
        return

    def readDelay(self, target):
        """
        Loop on reading the motor position until
        the 'unit' motor gets to the target position.
        Only call this when you're sure the motor is available and connected.

        :param: target - motor destination position
        :return: motor position in user steps, READERROR if error
        """

        global tk
        reps = 0
        atlimit = 0

        # how many times total we try
        maxTries = 5

        rp = self.getPosition()
        if DBG:
            print(f">>> readDelay IN {target} pos {rp}")

        if rp == READERROR:
            print(f"!!! readDelay: can't get motor position. RETURN")
            return READERROR

        delay = (abs(rp - target)) * 1.1 / self.speed
        if delay < 1.0:
             delay = 1.0
        ldelay = delay
        msg = f"Wait {int(10.0 * delay) / 10.0} sec"

        tk.Label(page[self.unit], font='Ariel 13', foreground="#FF0000", text=msg).place(x=90, y=10, width=350, height=25)

        while rp != target and rp != READERROR:
            reps += 1
            if DBG:
                print(f">>> readDelay: Unit {self.unit} attempt {reps}")

            delay = (abs(rp - target)) * 1.1 / self.speed
            if delay < 1.0:
                delay = 1.0
            """
            if ldelay < delay:
                if DBG:
                    print("!!! readDelay: Motor going in wrong direction")
                # do these 2 actually return a value we can check with isError()?
                self.client.write_register(0x7D, 0x20, unit=self.unit)
                self.client.write_register(0x7D, 0x0, unit=self.unit)
                break
            """
            if reps == maxTries:
                if DBG:
                    print(f"!!! readDelay: max tries exceeded moving from {rp} to {target}. Return")
                return READERROR

            if DBG:
                print(f">>> Wait {delay} sec to goto {target} from {rp} at speed {self.speed}")

            ldelay = delay
            # set a busy cursor
            main.config(cursor="wait")
            main.update()
            sleep(delay)

            rp = self.getPosition()
            T.setLabel(self.unit, rp)
            T.setTmpArr(self.unit, rp)
            
            print(f">>> readDelay: current pos is {rp}, target is {target}")
            main.config(cursor="")

            atlimit = self.checkLimits()
            if atlimit == READERROR:
                print(f"!!! readDelay: got atlimit readerror on unit {self.unit}. RETURN")
                return READERROR
            elif atlimit:
                print(f"!!! readDelay: at Limit for unit {self.unit}. RETURN")
                return ATLIMIT

        tk.Label(page[self.unit], font='Ariel 13', foreground="#F0F0F0", text=msg).place(x=90, y=10, width=350, height=25)
        if DBG:
            print(f">>> readDelay unit: {self.unit} out: {rp}")
        self.position = rp
        return rp

    def readMotor(self):
        """
		Read the position of the 'unit' motor. Manages its own connect/disconnct.

		:Return position or READERROR if any exceptions
		"""
        global tk
        position = READERROR # set this initially to an error. Is only reset if can be read.

        if TEST:
            self.position = 1000
            return self.position

        if self.connectMotor():
            position = self.getPosition()
            if position == READERROR:
                print(f"!!! - readMotor unit {self.unit}, can't get motor position.")
                self.closeMotor()
                return READERROR
        else:
            print(f"!!! - readMotor unit {self.unit}, connectMotor() failed.")
            # emergency close. not sure if this will propagate badly
            self.closeMotor()
            return READERROR

        self.position = position

        T.setLabel(self.unit, self.position)
        T.setTmpArr(self.unit, self.position)

        self.closeMotor()
        return self.position

    def getPosition(self):
        """
		Read the position of the 'unit' motor. Assumes motor is connected.

		:Return position or READERROR if any exceptions
		"""

        position = READERROR # set this initially to an error. Is only reset if can be read.
        hiPosition = loPosition = 0

        if TEST:
            return 1000

        read = self.client.read_holding_registers(0x00C6, 1, unit=self.unit)
        if read.isError():
            log.debug(read)
            print(f"!!! - getPosition unit {self.unit}, ioException on read.")
            return READERROR
        else:
            hiPosition = read.registers[0]
 
        read = self.client.read_holding_registers(0x00C7, 1, unit=self.unit)
        if read.isError():
            log.debug(read)
            print(f"!!! - getPosition unit {self.unit}, ioException on read.")
            return READERROR
        else:
            loPosition = read.registers[0]
        
        position = hiPosition * 65536 + loPosition
        return position

    def getTarget(self):
        """
        Get value in data entry window.
        Send motor to that value
        """
        location = T.getLabel(self.unit)

        self.target = location
        self.sendMotor(location)

        if DBG2:
            print("--- getTarget: GOT LOCATION", location)
        return

    # major rework, now includes better exception handling
    def sendMotor(self, location):
        """
        Send the 'unit' motor to the target location. Manages its own connection/disconnection.
        :return self.position if success, READERROR otherwise (exception errors)

        """
        pos = READERROR
        delta = 0
        rp = 0
        alarm = 0
        self.target = location

        if TEST:
            self.position = self.target
            # Location[self.unit] = self.position
            I.setEntry(self.unit, self.position)
            T.setLabel(self.unit, self.position)
            T.setTmpArr(self.unit, self.position)
            return self.position

        if DBG:
            print(f">>> sendMotor: Sending unit {self.unit}, to {self.position}")

        pos = self.readMotor()
        if pos == READERROR:
            # we couldn't read the motor!
            msg = f"Motor {self.unit} is not available"
            print(f"!!! sendMotor: could not read unit {self.unit}")
            message(self.unit, 1, msg)
            return READERROR

        delta = self.target - pos

        if delta == 0:
            return self.position

        if int(delta) > 0:
            if DBG2:
                print(f">>> sendMotor: Send Forward unit: {self.unit} from {self.position} to {self.target}")

        if int(delta) < 0:
            if DBG2:
                print(f">>> sendMotor: Send Reverse unit: {self.unit} from {self.position} to {self.target}")

        if self.outOfRange(delta):
            print("!!! sendMotor: SEND IS OUT OF RANGE. RETURN")
            return READERROR

        # get the desired target position
        setPosition = int(self.target)

        hiPosition = int(setPosition / 65536)
        lowPosition = setPosition % 65536

        if DBG:
            print(f">>> sendmMotor: Send unit {self.unit} TO {setPosition}")

        if self.connectMotor():
            # needs error checking against alarm
            alarm = self.chkAlrm()
            if alarm:
                self.showAlarm(alarm)

            if self.unit <= 20:
                self.client.write_register(0x7D, 0x20, unit=self.unit)
                self.client.write_register(0x1801, 1, unit=self.unit)
                self.client.write_register(0x1805, self.speed, unit=self.unit)
                self.client.write_register(0x1802, hiPosition, unit=self.unit)
                self.client.write_register(0x1803, lowPosition, unit=self.unit)
                self.client.write_register(0x7D, 0x8, unit=self.unit)
                rp = self.readDelay(setPosition)

                if rp == READERROR:
                    print("!!! sendMotor: bad result from readDelay! Return")
                    msg = "Motor " + str(self.unit) +" is not available"
                    message(self.unit, 1, msg)
                    self.closeMotor()
                    return READERROR
            else:
                self.client.write_register(0x7D, 0x20, unit=self.unit)
                self.client.write_register(0x7D, 0x0, unit=self.unit)
                self.client.write_register(0x1801, 1, unit=self.unit)
                self.client.write_register(0x1805, self.speed, unit=self.unit)
                self.client.write_register(0x1802, hiPosition, unit=self.unit)
                self.client.write_register(0x1803, lowPosition, unit=self.unit)
                self.client.write_register(0x7D, 0x8, unit=self.unit)

                rp = self.readDelay(setPosition)
                if rp == READERROR:
                    print("!!! sendMotor: bad result from readDelay! Return")
                    msg = "Motor " + str(self.unit) +" is not available"
                    message(self.unit, 1, msg)
                    self.closeMotor()
                    return READERROR

                self.client.write_register(0x7D, 0x20, unit=self.unit)
                self.client.write_register(0x7D, 0x0, unit=self.unit)
                self.client.write_register(0x1801, 1, unit=self.unit)
                self.client.write_register(0x1805, self.speed, unit=self.unit)
                self.client.write_register(0x1802, hiPosition, unit=self.unit)
                self.client.write_register(0x1803, lowPosition, unit=self.unit)
                self.client.write_register(0x7D, 0x8, unit=self.unit)

                rp = self.readDelay(setPosition)
                if rp == READERROR:
                    print("!!! sendMotor: bad result from readDelay! Return")
                    msg = "Motor " + str(self.unit) +" is not available"
                    message(self.unit, 1, msg)
                    self.closeMotor()
                    return READERROR
        else:
            print("!!! sendMotor: can't connect to unit {self.unit}. Return")
            return READERROR

        self.closeMotor()

        I.setEntry(self.unit, rp)
        T.setLabel(self.unit, rp)
        T.setTmpArr(self.unit, rp)

        self.position = rp
        if DBG:
            print(f">>> sendMotor {self.unit} {self.position} Speed {self.speed} succeeded")

        # all good, return the final position
        return rp

    def getGearing(self, gearBox):
        """
        Get the Electronic Gearing to adjust the resolution

        Resolution = 1000 X GearB / GearA * GearBox [= 100 for gratings]
        """

        gearA = 1
        gearB = 9

        self.resolution = int(1000 * gearA * gearB * gearBox)

        if TEST:
            return self.resolution

        if self.available:
            self.connectMotor()
            read = self.client.read_holding_registers(0x0381, 1, unit=self.unit)
            if read.isError():
                print("!!! getGearing: got modbus exception: ", ExceptionCodes.get(read.exception_code))
            else:
                gearA = read.registers[0]
            
            read = self.client.read_holding_registers(0x0383, 1, unit=self.unit)
            if read.isError():
                print("!!! getGearing: got modbus exception: ", ExceptionCodes.get(read.exception_code))
            else:
                gearB = read.registers[0]

            self.speed = self.speed * gearB / gearA
            if DBG2:
                print(f">>> getGearing: Speed {self.speed}")
            self.closeMotor()
        else:
            print("!!! getGearing: Unable to check motor status.")
            return READERROR

        # verify requested gearing is integer and adjust gearB if needed
        condition = 1000.0 * float(gearB) / float(gearA) * float(gearBox)
        if condition - int(condition) != 0:
            gearB = int(condition / 1000.0 * float(gearA) / float(gearBox))

        # check P/R
        PR = 1000.0 * float(gearB) / float(gearA)
        if PR < 100 or PR > 10000:
            print("!!! getGearing: Electronic gearing is not valid")
            return READERROR

        self.resolution = int(1000 * gearB / gearA * gearBox)
        
        if DBG:
            print(f">>> getGearing: Adjusted gearA to {gearA} gearB to {gearB}")
            print(f">>> getGearing: Motor {self.unit} Resolution {self.resolution}")

        return self.resolution

    def setMotor(self, _tab):
        """
		Set the motor target position using the location for the selected RadioButton.

		:param tab: Tab number
		:return: True if success, False otherwise
		"""
        unit = self.unit
        res = READERROR

        if unit == 1:
            location = [int(i[2]) for i in tab1][slide.get()]
        if unit == 2:
            location = [int(i[2]) for i in tab2][source.get()]
        if unit == 3:
            location = [int(i[2]) for i in tab3][grate1.get()]
        if unit == 4:
            location = [int(i[2]) for i in tab4][grate2.get()]
        self.target = location

        if DBG:
            print(f">>> setMotor: Unit {unit}, to {location}")
        # TODO: error trapping here

        res = self.sendMotor(location)

        if res == READERROR:
            print(f"!!! setMotor: Unit {unit}, to {location} failed.")
            return False
        else:
            return True

    def stopMotor(self):
        """
		Stop the motor

		:param unit: motor index number,
		:param tab: Tab number
		:return: None
		"""

        # should check this for errors if possible...
        if self.connected:
            self.client.write_register(0x7D, 0x20, unit=self.unit)
            self.client.write_register(0x7D, 0x0, unit=self.unit)
        else:
            print("!!! stopMotor: Can't stop motor - client not connected.")
            # try to kill current anyway
            self.client.write_register(0x251, 0x0, unit=self.unit)
            beep(2)
        return

class InputControl:
    """
    This class contains motor attributes and methods
    """

    def _init_(self):
        self.t = 0
        self.x = 0
        self.y = 0
        self.var = ''
        self.lstr = ''
        self.res = 0
        self.unit = 0

    def callback(self, var, t, x, y):
        """
        Retrieve result for Entry value.

        :param var: Entry variable
        :param t: Entry box for tab 't'
        :param x: Entry box x position
        :param y: Entry box y position
        :return: True/False
        """
        _val = str(var.get())

        if not _val:
            return

        if DBG2:
            print("CALLBACK", t, _val)
        try:
            int(_val)
        except:
            filter_char = lambda char: char.isdigit()
            _val = filter(filter_char, _val)
            if _val.find("-") > 0:
                _val = _val.replace("-", "")
            try:
                int(_val)
            except:
                return False

        if int(_val) < 0:
            _val = "0"
        
        if t == 1:
            upper = M1.upper
        elif t == 2:
            upper = M2.upper
        elif t == 3:
            upper = M3.upper
        elif t == 4:
            upper = M4.upper

        if int(_val) > upper:
            _val = str(upper)
        var.set(_val)

        self.setAngle(_val, t, x, y)

        return True


    def convertL2S(self, lstr):
        # initialization of string to ""
        new = ""

        # convert first level list to string
        #s = [item for sublist in l for item in sublist]
        _s = [str(i) for i in lstr]

        # traverse each list
        for line in _s:
            # traverse the string
            for x in line:
                if x in "['":
                    continue
                if x in ",":
                    new += '\t'
                    continue
                if x in "]":
                    new += '\n'
                    continue
                new += x

            # return string
        return new

    def convertS2Dms(self, _val, res):
        # convert a step value to degrees, minutes, seconds

        dg = float(int(_val)) * 360.0 / float(res)
        di = int(dg)
        mn = (dg - float(di)) * 60.0
        mi = int(mn)
        sc = (mn - float(mi)) * 60.0
        si = int(sc)
        if di == 0:
            st = str(abs(mi)) + "'" + str(abs(si)) + '"'
        else:
            st = str(di) + u"\u00b0" + str(abs(mi)) + "'" + str(abs(si)) + '"'
        if _val < 0:
            st = "-" + st
        return st

    def convertS2Dcd(self, _val, res):
        # convert a step value to decimal degrees

        dg = float(int(_val)) * 360.0 / float(res)
        st = str(dg)
        if _val < 0:
            st = "-" + st
        return st


    def convertS2(self, _val, res):
        # convert a step value to degrees, decimal minutes
        dg = float(int(_val)) * 360.0 / float(res)
        di = int(dg)
        mn = (dg - float(di)) * 60.0
        mn = int(100*mn)/100.0
        if mn - int(mn) < 0.05:
            #ln = len(str(mn))
            mn = int(mn)
        if di == 0:
            st = str(abs(mn)) + "'"
        else:
            if mn == 0:
                st = str(di) + u"\u00b0"
            else:
                st = str(di) + u"\u00b0" + str(abs(mn)) + "'"

        if _val < 0:
            st = "-" + st
        return st

    def initEntry(self, unit):
        global strv
        #import numpy as np

        #motors = np.asarray([0, M1, M2, M3, M4])
        motors = [0, M1, M2, M3, M4]
        rp = motors[unit].position
        #rp = Location[unit]
        strv = tk.StringVar()
        strv.set(rp)
        return

    def setAngle(self, _val, t, x, y):
        """
        Display the motor angle
        ANGLE DISPLAY WINDOW. tk.Label place sets x, y location
        """
        if t > 2:
            if t == 3:
                loc = M3.position - M3.reference
                st = I.convertS2Dcd(loc, M3.resolution)
            elif t == 4:
                loc = M4.position - M4.reference
                st = I.convertS2Dcd(loc, M4.resolution)

            str1 = tk.StringVar()
            str1.set(str(loc))
            str1.trace("w", lambda name, index, mode, sv=str1: I.callback(str1, t, 205, 145))
            e1 = tk.Label(page[t], font='Ariel 12', bg="#FFFFFF", text=st, justify='right')
            e1.place(x=x, y=y-50, width=80, height=20)
        return

    def is_number(self, var):
        """
        Test whether variable is a number.

        :param var:
        :return: True/False
        """
        try:
            if var == int(var):
                return True
        except:
            return False

    def setEntry(self, t, _val):
        """
        Get Entry values.

        :param t: tab number
        :param val: enter value
        :return:
        """
        global e, strv

        val = str(int(_val))
        if DBG2:
            print(f">>> setEntry: target location {t} VAL {val}")

        if t < 3:
            strv = tk.StringVar()
            strv.set(str(val))
            strv.trace("w", lambda name, index, mode, sv=strv: I.callback(strv, t, 215, 105))
            e[t] = tk.Entry(page[t], font='Ariel 12', textvariable=strv, bg="#FFFFFF", validate="focusout",
                            validatecommand=I.callback(strv, t, 215, 105), justify='right')
            e[t].place(x=245, y=175, width=60, height=20)
        if t > 2:
            str1 = tk.StringVar()
            str1.set(str(val))
        # POSITION DISPLAY WINDOW, "callback" sets x, y location
            str1.trace("w", lambda name, index, mode, sv=str1: I.callback(str1, t, 200, 100))
            e[t] = tk.Entry(page[t], font='Ariel 12', textvariable=str1, bg="#FFFFFF", validate="focusout",
                            validatecommand=I.callback(str1, t, 200, 100), justify='right')
        # POSITION ENTRY WINDOW, "place" sets x, y location
            e[t].place(x=210, y=150, width=60, height=20)
        return

class LocalIO:
    """
    Does LocalIO
    """

    def _init_(self, filename):
        self.filename = filename

    def readDflt(self):
        """
        Read the default tablet settings.
         .
        :return: defaults filename
        """
        # filename = askopenfilename(initialdir="./", title="Select file",
        #                                             filetypes=(("default files", "*.dft"), ("all files", "*.*")))
        global tab1, tab2, tab3, tab4
        global tmp1, tmp2, tmp3, tmp4
        global pos1, pos2, pos3, pos4
        global jog1, jog2, jog3, jog4

        filename = DFLT_POSIX
        fileHandle = open(filename, "r")
        records = fileHandle.readlines()
        fileHandle.close()

        j1 = j2 = j3 = j4 = 0
        t1 = t2 = t3 = t4 = 0
        for record in records:
            line = record.split()
            if line[1] == 'jog':
                if line[0] == str(1) and not j1:
                    j1 = 1
                    jog1 = []
                if line[0] == str(2) and not j2:
                    j2 = 1
                    jog2 = []
                if line[0] == str(3) and not j3:
                    j3 = 1
                    jog3 = []
                if line[0] == str(4) and not j4:
                    j4 = 1
                    jog4 = []
                if line[0] == str(1) and j1:
                    jog1.append(line)
                if line[0] == str(2) and j2:
                    jog2.append(line)
                if line[0] == str(3) and j3:
                    jog3.append(line)
                if line[0] == str(4) and j4:
                    jog4.append(line)
            else:
                if line[1] != 'res' and line[1] != 'ref':
                    if line[0] == str(1) and not t1:
                        t1 = 1
                        tab1 = []
                        tmp1 = []
                    if line[0] == str(2) and not t2:
                        t2 = 1
                        tab2 = []
                        tmp2 = []
                    if line[0] == str(3) and not t3:
                        t3 = 1
                        tab3 = []
                        tmp3 = []
                    if line[0] == str(4) and not t4:
                        t4 = 1
                        tab4 = []
                        tmp4 = []
                    if line[0] == str(1) and t1:
                        tab1.append(line)
                        tmp1.append(line)
                    if line[0] == str(2) and t2:
                        tab2.append(line)
                        tmp2.append(line)
                    if line[0] == str(3) and t3:
                        tab3.append(line)
                        tmp3.append(line)
                    if line[0] == str(4) and t4:
                        tab4.append(line)
                        tmp4.append(line)
                if line[1] == 'ref':
                    if line[0] == str(1):
                        M1.reference = int(line[2])
                    if line[0] == str(2):
                        M2.reference = int(line[2])
                    if line[0] == str(3):
                        M3.reference = int(line[2])
                    if line[0] == str(4):
                        M4.reference = int(line[2])

        pos1 = copy.deepcopy(tab1)
        pos2 = copy.deepcopy(tab2)
        pos3 = copy.deepcopy(tab3)
        pos4 = copy.deepcopy(tab4)

        tmp1 = copy.deepcopy(tab1)
        tmp2 = copy.deepcopy(tab2)
        tmp3 = copy.deepcopy(tab3)
        tmp4 = copy.deepcopy(tab4)


        if DBG2:
            print(f"Default file is: {filename}")

        main.title('GAP Motor Control: using ' + str(filename))
        main.title('DEFAULT settings: ' + str(filename))
        main.config()
        return filename

    def readConfig(self):
        """
        Read the default config settings.
        .
        :return:
        """

        fileHandle = open(CONFIG_FILENAME, "r")
        records = fileHandle.readlines()
        fileHandle.close()
        record = 0
        line = ''

        for record in records:
            line = record.split()
            if line[0] == '1':
                M1.offset = int(line[2])
                M1.zero = int(line[3])
                M1.speed = int(line[4])
                M1.lower = int(line[5])
                M1.upper = int(line[6])
            if line[0] == '2':
                M2.offset = int(line[2])
                M2.zero = int(line[3])
                M2.speed = int(line[4])
                M2.lower = int(line[5])
                M2.upper = int(line[6])
            if line[0] == '3':
                M3.offset = int(line[2])
                M3.zero = int(line[3])
                M3.speed = int(line[4])
                M3.lower = int(line[5])
                M3.upper = int(line[6])
            if line[0] == '4':
                M4.offset = int(line[2])
                M4.zero = int(line[3])
                M4.speed = int(line[4])
                M4.lower = int(line[5])
                M4.upper = int(line[6])

    def readUser(self):
        """
        Read user tablet settings.
         .
        :return: selected filename
        """
       
        # global pos1, pos2, pos3, pos4
        # item1, item2, item3, item4 = 0
        global tab1, tab2, tab3, tab4
        global tmp1, tmp2, tmp3, tmp4
        #global pos1, pos2, pos3, pos4
        global jog1, jog2, jog3, jog4

        filename = askopenfilename(initialdir="./", title="Select file",
                                   filetypes=(("config files", "*.usr"), ("all files", "*.*")))
        if not filename:
            return

        # read whole file
        fileHandle = open(filename, "r")
        records = fileHandle.readlines()
        fileHandle.close()

        j1 = j2 = j3 = j4 = 0
        t1 = t2 = t3 = t4 = 0
        # parse records into tabs
        for record in records:
            line = record.split()

            if line[1] == 'jog':
                if line[0] == str(1) and not j1:
                    j1 = 1
                    jog1 = []
                if line[0] == str(2) and not j2:
                    j2 = 1
                    jog2 = []
                if line[0] == str(3) and not j3:
                    j3 = 1
                    jog3 = []
                if line[0] == str(4) and not j4:
                    j4 = 1
                    jog4 = []
                if line[0] == str(1) and j1:
                    jog1.append(line)
                if line[0] == str(2) and j2:
                    jog2.append(line)
                if line[0] == str(3) and j3:
                    jog3.append(line)
                if line[0] == str(4) and j4:
                    jog4.append(line)
            else:
                if line[1] != 'res' and line[1] != 'ref':
                    if line[0] == str(1) and not t1:
                        t1 = 1
                        tab1 = []
                        tmp1 = []
                    if line[0] == str(2) and not t2:
                        t2 = 1
                        tab2 = []
                        tmp2 = []
                    if line[0] == str(3) and not t3:
                        t3 = 1
                        tab3 = []
                        tmp3 = []
                    if line[0] == str(4) and not t4:
                        t4 = 1
                        tab4 = []
                        tmp4 = []
                    if line[0] == str(1) and t1:
                        tab1.append(line)
                        tmp1.append(line)
                    if line[0] == str(2) and t2:
                        tab2.append(line)
                        tmp2.append(line)
                    if line[0] == str(3) and t3:
                        tab3.append(line)
                        tmp3.append(line)
                    if line[0] == str(4) and t4:
                        tab4.append(line)
                        tmp4.append(line)
                if line[1] == 'ref':
                    if line[0] == str(1):
                        M1.reference = int(line[2])
                    if line[0] == str(2):
                        M2.reference = int(line[2])
                    if line[0] == str(3):
                        M3.reference = int(line[2])
                    if line[0] == str(4):
                        M4.reference = int(line[2])

        filename = path.basename(filename)
        main.title('GAP Motor Control: using ' + str(filename))
        main.title('USER settings: ' + str(filename))
        if DBG2:
            print(f">>> readUser: USER {tab2}")
            print(f">>> readUser: {filename}")

        #
        # since this calls run() isn't this recursive? should it be -egs-
        updateTabs()
        return

    def saveUser(self):
        """
        Save settings for current user.

        :return:
        """
        #T.updateTabLocations()

        filename = asksaveasfilename(initialdir="./", title="Select file",
                                     filetypes=(("config files", "*.usr"), ("all files", "*.*")))

        # define file
        ttl1 = "# GAPMC configuration\n"
        ttl2 = "#tab \t key \t value \t labels\n"
        hdr1 = "#1 \t tab \t 1 \t Slide\n"
        hdr2 = "#2 \t tab \t 2 \t Comparisons\n"
        hdr3 = "#3 \t tab \t 3 \t Grating 1\n"
        hdr4 = "#4 \t tab \t 4 \t Grating 2\n"
        str1 = I.convertL2S(tmp1)
        str2 = I.convertL2S(tmp2)
        str3 = I.convertL2S(tmp3)
        str4 = I.convertL2S(tmp4)

        # build file
        records = []
        records.append(ttl1)
        records.append(ttl2)
        records.append(hdr1)
        records.append(str1)
        records.append(hdr2)
        records.append(str2)
        records.append(hdr3)
        records.append(str3)
        records.append(hdr4)
        records.append(str4)

        if filename == '':
            return
        # write file
        fileHandle = open(filename, "w")
        fileHandle.writelines(records)
        fileHandle.close()
        if DBG2:
            print(f">>> saveUser saved: {filename}")
        return

    def chkPassword(self, root, pw):
        """
        Verify password
        """
        if pw.get() == 'abc123' or pw.get() == 'OOS39023' or pw.get() == '123abc':
            root.destroy()
            F.setConfig()
        return

    def getPassword(self):
        """
        Pop pw entry window
        :return:
        """

        pswd = tk.Tk()
        pswd.wm_title('Password')
        pw = Canvas(pswd, width=300, height=60)
        pw.pack()
        pw.rowconfigure(0, {'minsize' : 20})
        pw.rowconfigure(2, {'minsize' : 20})
        pw.columnconfigure(0, {'minsize' : 50})
        pw.columnconfigure(2, {'minsize' : 50})
        pw.columnconfigure(4, {'minsize' : 50})
        pw.columnconfigure(6, {'minsize' : 50})

        tk.Label(pw, font='Ariel 13', text="Password").grid(row=1, column=1)
        rs = tk.StringVar()
        rs = tk.Entry(pw, font='Ariel 13', width=10, justify=RIGHT, borderwidth=2)
        rs.grid(row=1, column=3)
        b1 = tk.Button(pw, text="Enter", font='Ariel 13', command=partial(F.chkPassword, pswd, rs), pady=2, height=0, width=4, relief='ridge')
        b1.grid(row=1, column=5)

        pswd.mainloop()

    def saveCfg(self, win):
        """
        Save configurations for cmotors.

        :return:
        """

        filename = CONFIG_POSIX

        # define file
        ttl1 = "# Motor configurations\n"
        ttl2 = "# Motor  label \t"
        hdr1 = "\t 1 \t Slide \t\t"
        hdr2 = "\t 2 \t Comparison "
        hdr3 = "\t 3 \t Grating_1 \t"
        hdr4 = "\t 4 \t Grating_2 \t"
        hdr5 = "\t\toffset \tzero \tspeed \tlower \tupper \n"

        str1 = "\t" + str(o[1].get()) + "\t\t" + str(z[1].get()) + "\t\t" + str(s[1].get()) + "\t" + str(l[1].get()) + "\t\t" + str(u[1].get()) + "\n"
        str2 = "\t" + str(o[2].get()) + "\t\t" + str(z[2].get()) + "\t\t" + str(s[2].get()) + "\t" + str(l[2].get()) + "\t\t" + str(u[2].get()) + "\n"
        str3 = "\t" + str(o[3].get()) + "\t\t" + str(z[3].get()) + "\t\t" + str(s[3].get()) + "\t" + str(l[3].get()) + "\t\t" + str(u[3].get()) + "\n"
        str4 = "\t" + str(o[4].get()) + "\t\t" + str(z[4].get()) + "\t\t" + str(s[4].get()) + "\t" + str(l[4].get()) + "\t\t" + str(u[4].get()) + "\n"

        # build file
        records = []
        records.append(ttl1)
        records.append(ttl2)
        records.append(hdr5)

        records.append(hdr1)
        records.append(str1)
        records.append(hdr2)
        records.append(str2)
        records.append(hdr3)
        records.append(str3)
        records.append(hdr4)
        records.append(str4)

        # write file
        fileHandle = open(filename, "w")
        fileHandle.writelines(records)
        fileHandle.close()

        if DBG:
            print(f">>> saveCfg: wrote {filename}")

        # reset current values
        for motor in [M1, M2, M3, M4]:
            i = motor.unit
            motor.offset = int(o[i].get())
            motor.zero = int(z[i].get())
            motor.speed = int(s[i].get())
            motor.lower = int(l[i].get())
            motor.upper = int(u[i].get())

        win.destroy()

    def setConfig(self):
        """

        :return:
        """
        conf = tk.Tk()
        conf.wm_title('Settings')
        page[0] = Canvas(conf, width=850, height=280)
        page[0].grid()
        page[0].rowconfigure(0, {'minsize' : 20})
        page[0].rowconfigure(3, {'minsize' : 20})
        page[0].rowconfigure(8, {'minsize' : 20})
        page[0].rowconfigure(10, {'minsize' : 20})
        #page[0].rowconfigure(11, {'minsize' : 20})
        #page[0].rowconfigure(13, {'minsize' : 20})
        page[0].columnconfigure(0, {'minsize' : 50})
        page[0].columnconfigure(2, {'minsize' : 50})
        page[0].columnconfigure(4, {'minsize' : 50})
        page[0].columnconfigure(6, {'minsize' : 50})
        page[0].columnconfigure(8, {'minsize' : 50})
        page[0].columnconfigure(10, {'minsize' : 50})
        page[0].columnconfigure(12, {'minsize' : 50})

        tk.Label(page[0], text="MOTOR").grid(row=1, column=1)
        tk.Label(page[0], text="SLIDER").grid(row=4, column=1)
        tk.Label(page[0], text="COMPARISON").grid(row=5, column=1)
        tk.Label(page[0], text="GRATING 1").grid(row=6, column=1)
        tk.Label(page[0], text="GRATING 2").grid(row=7, column=1)

        tk.Label(page[0], text="HOME").grid(row=1, column=3)
        tk.Label(page[0], text="Position").grid(row=2, column=3)
        z[1] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        z[2] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        z[3] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        z[4] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        z[1].insert(0, M1.zero)
        z[2].insert(0, M2.zero)
        z[3].insert(0, M3.zero)
        z[4].insert(0, M4.zero)
        z[1].grid(row=4, column=3)
        z[2].grid(row=5, column=3)
        z[3].grid(row=6, column=3)
        z[4].grid(row=7, column=3)

        tk.Label(page[0], text="OFFSET").grid(row=2, column=5)
        tk.Label(page[0], text="Zero").grid(row=1, column=5)
        o[1] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        o[2] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        o[3] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        o[4] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        o[1].insert(0, M1.offset)
        o[2].insert(0, M2.offset)
        o[3].insert(0, M3.offset)
        o[4].insert(0, M4.offset)
        o[1].grid(row=4, column=5)
        o[2].grid(row=5, column=5)
        o[3].grid(row=6, column=5)
        o[4].grid(row=7, column=5)

        tk.Label(page[0], text="Motor").grid(row=1, column=7)
        tk.Label(page[0], text="SPEED").grid(row=2, column=7)
        s[1] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        # if s[1] > 5000:
        #     s[1] = 5000
        #     msg = "Speed limit is 5000"
        #     tk.Label(conf, font='Ariel 13' , foreground="C0C0C0", text=msg).place(x=100, y=240, width=350, height=25)
        s[2] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        s[3] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        s[4] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        s[1].insert(0, M1.speed)
        s[2].insert(0, M2.speed)
        s[3].insert(0, M3.speed)
        s[4].insert(0, M4.speed)
        s[1].grid(row=4, column=7)
        s[2].grid(row=5, column=7)
        s[3].grid(row=6, column=7)
        s[4].grid(row=7, column=7)

        tk.Label(page[0], text="LOWER").grid(row=1, column=9)
        tk.Label(page[0], text="Limit").grid(row=2, column=9)
        l[1] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        l[2] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        l[3] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        l[4] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        l[1].insert(0, 0)
        l[2].insert(0, 0)
        l[3].insert(0, 0)
        l[4].insert(0, 0)
        l[1].grid(row=4, column=9)
        l[2].grid(row=5, column=9)
        l[3].grid(row=6, column=9)
        l[4].grid(row=7, column=9)

        tk.Label(page[0], text="UPPER").grid(row=1, column=11)
        tk.Label(page[0], text="Limit").grid(row=2, column=11)
        u[1] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        u[2] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        u[3] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        u[4] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        u[1].insert(0, M1.upper)
        u[2].insert(0, M2.upper)
        u[3].insert(0, M3.upper)
        u[4].insert(0, M4.upper)
        u[1].grid(row=4, column=11)
        u[2].grid(row=5, column=11)
        u[3].grid(row=6, column=11)
        u[4].grid(row=7, column=11)

        b1 = tk.Button(page[0], text="Save", font=6, command=partial(F.saveCfg, conf), pady=2, height=0, width=4, relief='ridge')
        b2 = tk.Button(page[0], text="Cancel", font=6, command=partial(conf.destroy), padx=2, height=0, width=6, relief='ridge')
        b1.grid(row=9, column=9)
        b2.grid(row=9, column=3)

        conf.mainloop()

class TabControl:
    """
    Control Tabs
    """
    def getLabel(self, t):
        """
        Get the entered value.

        :param unit: motor index number
        :return: Entry value
        """
        global e

        if e[t] != 0:
            ss = e[t].get()
        else:
            ss = 0
        return int(ss)

    def getRadioButn(self, unit, tablist):
        """
        Gets the RadioButton that matches the motor position.

        :param unit: motor index number
        :param tablist: contents array for the selected tablet
        :return: the RadioButton number found
        """

        if unit == 1:
            position = M1.readMotor()
            closest = T.getClosest(unit, position, tab1)
        if unit == 2:
            position = M2.readMotor()
            closest = T.getClosest(unit, position, tab2)
        if unit == 3:
            position = M3.readMotor()
            closest = T.getClosest(unit, position, tab3)
        if unit == 4:
            position = M4.readMotor()
            closest = T.getClosest(unit, position, tab4)

        if DBG2:
            print("GET Radio >>> ", unit, closest, position)
        return closest

    def getClosest(self, unit, position, tablist):
        """
        Gets the RadioButton that matches the motor position.

        :param unit: motor index number
        :param tablist: contents array for the selected tablet
        :param page: associated page number for the tablist
        :return: the RadioButton number found
        """

        if DBG2:
            print(tablist)

        list_of_numbers = [int(i[2]) for i in tablist]
        closest = min(enumerate(list_of_numbers), key=lambda ix: (abs(ix[1] - position)))[0]

        return closest

    def resetTab(self):
        """
        Reset settings to the llast file opened.

        :return: None
        """
        global tmp1, tmp2, tmp3, tmp4
        global tab1, tab2, tab3, tab4

        tab1 = copy.deepcopy(tmp1)
        tab2 = copy.deepcopy(tmp2)
        tab3 = copy.deepcopy(tmp3)
        tab4 = copy.deepcopy(tmp4)

    def setLabel(self, t, position, x=215, y=100):
        """
        Display the motor position
        CURRENT POSITION WINDOW, tk.Label place sets x, y location
        """
        global e1

        try:
            if t < 3:
                e1 = tk.Label(page[t], font='Ariel 12', bg="#FFFFFF", text=position, justify='right')
                e1.place(x=x + 20, y=y, width=60, height=20)
            if t > 2:
                e1 = tk.Label(page[t], font='Ariel 12', bg="#FFFFFF", text=position, justify='right')
                e1.place(x=x - 5, y=y, width=60, height=20)
                #e1.place(x=210, y=195, width=60, height=20)
        except:
            return

    def setLimits(self):
        """
        Toggle show/hide limits
        """

        global limitSet

        if limitSet == 'Show':
            limitSet = 'Hide'
        else:
            limitSet = 'Show'
        filemenu.entryconfig(2, label=limitSet + " Limits")

    def setTmpArr(self, unit, position):
        """
        Update Temporary Array for User Position Tweeks

        :param unit:
        :param position:
        :param closest:
        :return:
        """
        global tab1, tab2, tmp1, tmp2

        if unit == 1:
            closest = T.getClosest(unit, position, tab1)
            tmp1[closest][2] = position
            tab1 = copy.deepcopy(tmp1)
        if unit == 2:
            closest = T.getClosest(unit, position, tab2)
            tmp2[closest][2] = position
            tab2 = copy.deepcopy(tmp2)


class MakeTab:
    '''
    '''
    def _init_(self, unit):
        self.unit = unit

    def getIntegerRatio(self, resolution):
        """
         # find smallest ratio of integers
         ### MUST DIVIDE BY GEAR BOX RATIO = 100
         ### SINCE IT IS NOT DIVISIBLE
        """
        if DBG:
            print(">>> getIntegerRatio Res: ", resolution, resolution/360)
        stp = 1
        deg = 1
        for n in range(1, 360):
            if (resolution * n) % 360 == 0:
                stp = resolution * n / 360
                deg = n
                break
        return str(int(stp)), str(deg)

    def tablet1(self):
        """
        Display tablet 1 for motor number 'unit'.

        :param unit: motor index number.
        :return:
        """

        nb.add(page[1], text="Slide", sticky='NESW')

        jogN = len(jog1)
        jogR = jogN * 20
        jogS = 110 - jogR / 4

        tk.Label(page[1], font='Ariel 13', text="Current location").place(x=190, y=70, width=150, height=25)
        tk.Label(page[1], font='Ariel 13', text="Enter new location").place(x=190, y=140, width=150, height=25)
        tk.Label(page[1], font='Ariel 13', text="Jog").place(x=350, y=jogS, width=150, height=25)

        row = 0
        for line in tab1:
            if line[1] != 'tab' and line[1] != 'res' and line[1] != 'ref':
                if len(line) == 5:
                    name = line[3] + " " + line[4]
                else:
                    name = line[3]
                #butn="rb" + str(row)
                tk.Radiobutton(page[1], font='Ariel 13', text=name, command=partial(M1.setMotor, 1), padx=20,
                               variable=slide, value=row, anchor='w').place(x=20, y=jogS+20+20*row, width=150, height=25)
                row = row + 1

        row1 = 0; row2 = 0
        for line in jog1:
            if line[1] == 'jog':
                if int(line[2]) < 0:
                    ##print(line[2])
                    tk.Button(page[1], font='Ariel 12', text=line[3], command=partial(M1.jogMotor, line[2]), padx=40,
                              relief='ridge').place(x=380, y=jogS+30+row1*20, width=50, height=22)
                    row1 = row1 + 1
                if int(line[2]) > 0:
                    tk.Button(page[1], font='Ariel 12', text=line[3], command=partial(M1.jogMotor, line[2]), padx=40,
                              relief='ridge').place(x=428, y=jogS+30+row2*20, width=50, height=22)
                    row2 = row2 + 1

        tk.Button(page[1], font='Ariel 13', text="Go", command=partial(M1.getTarget), padx=40).place(x=215, y=175, width=30, height=20)

    def tablet2(self):
        """
        Display tablet 2 for motor number 'unit'.

        :param unit: motor index number.
        :return:
        """

        nb.add(page[2], text="Comparisons", sticky='NESW')

        jogN = len(jog2)
        jogR = jogN * 20
        jogS = 110 - jogR / 4

        tk.Label(page[2], font='Ariel 13', text="Current location").place(x=190, y=70, width=150, height=25)
        tk.Label(page[2], font='Ariel 13', text="Enter new location").place(x=190, y=140, width=150, height=25)
        tk.Label(page[2], font='Ariel 13', text="Jog").place(x=350, y=jogS, width=150, height=25)

        row = 0
        for line in tab2:
            if line[1] != 'tab' and line[1] != 'res' and line[1] != 'ref':
                if len(line) == 5:
                    name = line[3] + " " + line[4]
                else:
                    name = line[3]
                tk.Radiobutton(page[2], font='Ariel 13', text=name, command=partial(M2.setMotor, 2), padx=20,
                               variable=source, value=row, anchor='w').place(x=20, y=jogS+25+20*row, width=150, height=25)
                row = row + 1

        row1 = 0; row2 = 0
        for line in jog2:
            if line[1] == 'jog':
                if int(line[2]) < 0:
                    tk.Button(page[2], font='Ariel 12', text=line[3], command=partial(M2.jogMotor, line[2]), padx=40,
                              relief='ridge').place(x=380, y=jogS+30+row1*20, width=50, height=22)
                    row1 = row1 + 1
                if int(line[2]) > 0:
                    tk.Button(page[2], font='Ariel 12', text=line[3], command=partial(M2.jogMotor, line[2]), padx=40,
                              relief='ridge').place(x=428, y=jogS+30+row2*20, width=50, height=22)
                    row2 = row2 + 1

        tk.Button(page[2], font='Ariel 13', text="Go", command=partial(M2.getTarget), padx=40).place(x=215, y=175, width=30, height=20)

    def tablet3(self):
        """
        Display tablet 3 for motor number 'unit'.

        :param unit: motor index number.
        :return:
        """
        #global Resolution, Reference

        steps, degree = self.getIntegerRatio(M3.resolution)

        stepPerDegree = int(steps) / int(degree)
        stepPerMin = (stepPerDegree / 60) * 100
        msg = str.format("{} steps per minute", stepPerMin)
        nb.add(page[3], text="Grating 1", sticky='NESW')

        jogN = len(jog3); jogR = jogN * 20; jogS = 110 - jogR / 4

        tk.Label(page[3], font='Ariel 13', text="Grating 1 angle is").place(x=30, y=50, width=150, height=25)
        tk.Label(page[3], font='Ariel 13', text="Current location").place(x=30, y=100, width=150, height=25)
        tk.Label(page[3], font='Ariel 13', text="Enter new location").place(x=30, y=150, width=150, height=25)
        tk.Label(page[3], font='Ariel 13', text="Jog").place(x=350, y=jogS, width=150, height=25)
        tk.Label(page[3], font=10, text=steps + " steps per " + degree + u"\u00b0").place(x=30, y=200, width=150, height=25)
        #tk.Label(page[3], font=10, text=msg).place(x=30, y=200, width=150, height=25)

        row = 0
        for line in tab3:
            if line[1] != 'tab' and line[1] != 'res' and line[1] != 'ref':
                if len(line) == 5:
                    name = line[3] + " " + line[4]
                else:
                    name = line[3]
                tk.Radiobutton(page[3], font='Ariel 13', text=name, command=partial(M3.setMotor, 3), padx=20,
                               variable=grate1, value=row, anchor='w').place(x=20, y=50+20*row, width=150, height=25)
                row = row + 1
            if line[1] == 'res':
                M3.resolution = int(line[2])
                if line[1] == 'ref':
                    M3.reference = int(line[2])
                
        row1 = 0; row2 = 0
        for line in jog3:
            if line[1] == 'jog':
                if int(line[2]) < 0:
                    tk.Button(page[3], font='Ariel 12', text=line[3], command=partial(M3.jogMotor, line[2]), padx=40,
                              relief='ridge').place(x=380, y=jogS+30+row1*20, width=50, height=22)
                    row1 = row1 + 1
                if int(line[2]) > 0:
                    tk.Button(page[3], font='Ariel 12', text=line[3], command=partial(M3.jogMotor, line[2]), padx=40,
                              relief='ridge').place(x=428, y=jogS+30+row2*20, width=50, height=22)
                    row2 = row2 + 1

        tk.Button(page[3], font='Ariel 13', text="Go", fg="red", command=partial(M3.getTarget), padx=40).place(x=275, y=150, width=30, height=20)
        return

    def tablet4(self):
        """
        Display tablet 4 for motor number 'unit'.

        :param unit: motor index number.
        :return:
        """
        
        steps, degree = self.getIntegerRatio(M4.resolution)

        nb.add(page[4], text="Grating 2", sticky='NESW')

        jogN = len(jog4)
        jogR = jogN * 20
        jogS = 110 - jogR / 4

        tk.Label(page[4], font='Ariel 13', text="Grating 2 angle is").place(x=30, y=50, width=150, height=25)
        tk.Label(page[4], font='Ariel 13', text="Current location").place(x=30, y=100, width=150, height=25)
        tk.Label(page[4], font='Ariel 13', text="Enter new location").place(x=30, y=150, width=150, height=25)
        tk.Label(page[4], font='Ariel 13', text="Jog").place(x=350, y=jogS, width=150, height=25)
        tk.Label(page[4], font=10, text=steps + " steps per " + degree + u"\u00b0").place(x=30, y=200, width=150, height=25)

        row = 0
        for line in tab4:
            if line[1] != 'tab' and line[1] != 'res' and line[1] != 'ref':
                if len(line) == 5:
                    name = line[3] + " " + line[4]
                else:
                    name = line[3]
                tk.Radiobutton(page[4], font='Ariel 13', text=name, command=partial(M4.setMotor, 4), padx=20,
                               variable=grate2, value=row, anchor='w').place(x=20, y=75+20*row, width=150, height=25)
                row = row + 1
            if line[1] == 'res':
                M4.resolution = int(line[2])
            if line[1] == 'ref':
                M4.reference = int(line[2])

        row1 = 0; row2 = 0
        for line in jog4:
            if line[1] == 'jog':
                if int(line[2]) < 0:
                    tk.Button(page[4], font='Ariel 12', text=line[3], command=partial(M4.jogMotor, line[2]), padx=40,
                              relief='ridge').place(x=380, y=jogS+30+row1*20, width=50, height=22)
                    row1 = row1 + 1
                if int(line[2]) > 0:
                    tk.Button(page[4], font='Ariel 12', text=line[3], command=partial(M4.jogMotor, line[2]), padx=40,
                              relief='ridge').place(x=428, y=jogS+30+row2*20, width=50, height=22)
                    row2 = row2 + 1

        tk.Button(page[4], font='Ariel 13', text="Go", fg="red", command=partial(M4.getTarget), padx=40).place(x=275, y=150, width=30, height=20)

    def warntab(self, unit):
        """
        Display warning for motor number 'unit'.

        :param unit: motor index number.
        :return:
        """
        import tkinter.font as tkFont

        page[unit] = tk.Frame(nb, bg="#FFCCCC")
        nb.add(page[unit], text="WARNING", sticky='NESW')

        if unit == 1:
            motor = "Slide"
        if unit == 2:
            motor = "Comparison"
        if unit == 3:
            motor = "Grating 1"
        if unit == 4:
            motor = "Grating 2"
        warn1 = "Warning for " + motor
        warn2 = "Motor # " + str(unit) + " is NOT available."
        warn3 = "Check all cable connections."
        warn4 = "Check for power to motor."
        warn5 = "Diagnose lights on units."
        fontStyle = tkFont.Font(family="Lucida Grande", size=18)
        tk.Label(page[unit], font=fontStyle, text=warn1, fg="#CC0000", bg="#FFCCCC").place(x=90, y=50, width=350, height=25)
        tk.Label(page[unit], font='Ariel 13', text=warn2, bg="#FFCCCC").place(x=90, y=90, width=350, height=25)
        tk.Label(page[unit], font='Ariel 13', text=warn3, bg="#FFCCCC").place(x=90, y=120, width=350, height=25)
        tk.Label(page[unit], font='Ariel 13', text=warn4, bg="#FFCCCC").place(x=90, y=150, width=350, height=25)
        tk.Label(page[unit], font='Ariel 13', text=warn5, bg="#FFCCCC").place(x=90, y=180, width=350, height=25)

"""
Main loop, initialize.
"""
# global variables
# com ports
ports = list(serial.tools.list_ports.comports())

if DBG2:
    print(f">>> Ports: {ports}")
    i = 0
    for p, q, r in ports:
        i += 1
        if r.find("FTDIBUS") >= 0:
            print(f">>> RS485 P {p}, Q {q}, R {r}")
            port485 = p
        else:
            print(f">>> Found Motor {i} port {p}")

"""
Motor check.
"""

# do full initialization of the objects
port485 = "COM14"

M1 = MotorControl(1, port485, 1000, 0, 3000, 0, 8000, 1000, 0, 8000, 1)
M2 = MotorControl(2, port485, 100, 0, 0, 0, 1000, 1000, 0, 1000, 1)
M3 = MotorControl(3, port485, 10000, 0, 1000, 0, 125000, 100000, 0, 15000, 100)
M4 = MotorControl(4, port485, 10000, 0, 1000, 0, 125000, 100000, 0, 15000, 100)

if not TEST and not (M1.available or M2.available or M3.available or M4.available):
    warn()
    sys.exit()

F = LocalIO()
F.readConfig()

"""
Main loop, begin.
"""
main = tk.Tk()
main.wm_title('GAP Motor Control')
main.geometry('550x300')
menubar = tk.Menu(main)
menu()

# Gets both half the screen width/height and window width/height
_positionRight = int(main.winfo_screenwidth()/2 - main.winfo_reqwidth()/1)
_positionDown = int(main.winfo_screenheight()/2 - main.winfo_reqheight()/1)

# Positions the window in the center of the page.
main.geometry(f"+{_positionRight}+{_positionDown}")

# display the menu
main.config(menu=menubar)

B = MakeTab()
I = InputControl()
T = TabControl()

# Global variables
strv = tk.StringVar()
str1 = tk.StringVar()
str2 = tk.StringVar()

fname = F.readDflt()

slide = tk.IntVar()
source = tk.IntVar()
grate1 = tk.IntVar()
grate2 = tk.IntVar()

rows = 0
while rows < 50:
    main.rowconfigure(rows, weight=1)
    main.columnconfigure(rows, weight=1)
    rows += 1

"""
Create notepad tabs
"""
nb = ttk.Notebook(main)
nb.grid(row=1, column=0, columnspan=50, rowspan=49, sticky='NESW')

"""
Initialize the tabs
"""
svar = tk.StringVar()

run()
main.mainloop()
"""
End main loop
"""
