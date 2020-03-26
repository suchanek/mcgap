#
#
import tkinter as tk
from tkinter import *
from tkinter.filedialog   import askopenfilename
from tkinter.filedialog   import asksaveasfilename
from tkinter import ttk
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

from pymodbus.exceptions import ModbusIOException as ModbusException
from pymodbus.exceptions import ConnectionException as ConnException

FORMAT = ('%(asctime)-15s %(threadName)-15s '
          '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')

logging.basicConfig(format=FORMAT)
log = logging.getLogger()

from pymodbus.client.sync import ModbusSerialClient as ModbusClient

# Define Global Variables
filemenu = 0
_warn1 = ''
_mode = 0
limitSet = "Show"
# i don't know if this is right but DISABLE is used and wasn't defined globally
DISABLE = 0
TEST = 0
DBG = 1
DBG2 = 0

mflag = 0

Reference = [0,0,0,0,0]
Location = [0, 0, 0, 0, 0] # array of current coordinates

Zero = [0, 3000, 0, 1000, 1000]
Speed = [0, 100, 100, 10000, 10000]
Resolution = [0,1000,1000,100000,100000]
Upper = [0, 8000, 1000, 12500, 150000]
Offset = [0, 8000, 1000, 15000, 15000]

# Initialize arrays
e = [0,0,0,0,0,0,0,0]
l = [0,0,0,0,0]
o = [0,0,0,0,0]
s = [0,0,0,0,0]
u = [0,0,0,0,0]
z = [0,0,0,0,0]
_run = []

e1 = e2 = ''
tab = 0
key = ''
val = 0
label = ''
jog1 = []
jog2 = []
jog3 = []
jog4 = []
tab1 = []
tab2 = []
tab3 = []
tab4 = []
tmp1 = []
tmp2 = []
tmp3 = []
tmp4 = []
pos1 = ""
pos2 = ""
pos3 = ""
pos4 = ""
page = ["page[0]", "page[1]", "page[2]", "page[3]", "page[4]"]

_ref = []
_res = []

import serial.tools.list_ports

ports = list(serial.tools.list_ports.comports())
"""
for p,q,r in ports:
    if "USB" in q:
        continue
    #com = int(filter(str.isdigit, p))
    com = filter(str.isdigit, p)
    if DBG:
      print("P",p,com)
"""

PATH = pathlib.Path(__file__).parent.joinpath("").resolve()
CONFIG_FILENAME = "GAPMC.ozs"
CONFIG_PATH = PATH.joinpath(CONFIG_FILENAME)
CONFIG_POSIX = CONFIG_PATH.as_posix()

DFLT_FILENAME = "GAPMC.dft"
DFLT_PATH = PATH.joinpath(DFLT_FILENAME)
DFLT_POSIX = DFLT_PATH.as_posix()


def exit():
    """
    Provides a single exit point.

    Will test for changes and ask if changes should be saved.

    return:
    """
    sys.exit(10)
    return None

def menu():
    """
    Create a pulldown file menu, and add it to the menu bar
    """
    global filemenu

    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Open User Settings", command=F.readUser)
    filemenu.add_command(label="Save User Settings", command=F.saveUser)
    #filemenu.add_command(label=limitSet + " Limits", command=T.setLimits)
    #filemenu.add_command(label="Reset to Prev Tablets", command=T.resetTab)
    filemenu.add_command(label="Reset to Orig Defaults", command=F.readDflt)
    filemenu.add_command(label="Configure Motors", command=F.getPassword)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=main.quit)
    menubar.add_cascade(label="File", menu=filemenu)

def message(unit, mflag, msg):
    if mflag == 1:
        if DBG2:
            print(unit,"MESSAGE:",msg,">",page[unit],"<")
        tk.Label(page[unit], font=20, foreground="#000000", text=msg).place(x=100, y=10, width=350, height=25)
        mflag = 0
    else:
        if DBG2:
            print(unit,"MESSAGE:",msg,">",page[unit],"<")
        tk.Label(page[unit], font=20, foreground="#F0F0F0", text=msg).place(x=100, y=10, width=350, height=25)


def warn():
    warn2 = "No motor is available."
    warn3 = "Connect and turn on motors."
    temp = tk.Tk()
    temp.wm_title('WARNING')
    w = Canvas(temp, width=340, height=150)
    w.pack()
    w.create_text(170,15,text='WARNING:',font=20,fill="#FF0000")
    w.create_text(170,45,text=warn2,font=20)
    w.create_text(170,75,text=warn3,font=20)
    windowWidth = temp.winfo_reqwidth()
    windowHeight = temp.winfo_reqheight()
    positionRight = int(temp.winfo_screenwidth()/2 - windowWidth/1)
    positionDown = int(temp.winfo_screenheight()/2 - windowHeight/1)

    # temp.geometry("+{}+{}".format(positionRight, positionDown))
    temp.geometry(f'+{positionRight}+{positionDown}')

    b = tk.Button(w, text='QUIT', font=30, width=35, command=exit, anchor=S) 
    b.configure(width=10, activebackground="#BBBBBB")
    bw = w.create_window(120, 110, anchor=NW, window=b)
    b.place(x=120,y=110)
    temp.mainloop()

    exit()

def run():
    global nb
    if M1.connected:
        page[1] = ttk.Frame(nb)
        B.tablet1()
        p1=M1.readMotor()
        if not p1:
            # put up a warning that M1 can't be read...
            print("Can't read unit ", M1.unit)
            msg = f"Motor {M1.unit} is not available"
            mflag = 1
            message(M1.unit,mflag,msg)
        else:
            I.setEntry(1, p1)
            slidePos = T.getRadioButn(1, tab1, page[1])
            slide.set(slidePos)
    else:
        page[1] = ttk.Frame(nb)
        msg = f"Motor {M1.unit} is not available"
        mflag = 1
        message(M1.unit,mflag,msg)
    if M2.connected:
        page[2] = ttk.Frame(nb)
        B.tablet2()
        p2=M2.readMotor()
        if not p2:
            # put up a warning that M1 can't be read...
            print("Can't read unit ", M2.unit)
            msg = f"Motor {M2.unit} is not available"
            mflag = 1
            message(M2.unit,mflag,msg)
        else:
            I.setEntry(2 ,p2)
            cmparPos = T.getRadioButn(2, tab2, page[2])
            source.set(cmparPos)
    else:
        page[2] = ttk.Frame(nb)
        msg = f"Motor {M1.unit} is not available"
        mflag = 1
        message(M2.unit,mflag,msg)
    if M3.connected:
        page[3] = ttk.Frame(nb)
        B.tablet3()
        p3=M3.readMotor()
        if not p3:
            # put up a warning that M1 can't be read...
            print("Can't read unit ", M3.unit)
            msg = f"Motor {M3.unit} is not available"
            mflag = 1
            message(M3.unit,mflag,msg)
        else:
            I.setEntry(3, p3)
            grat1Pos = T.getRadioButn(3, tab3, page[3])
            grate1.set(grat1Pos)
    else:
        page[3] = ttk.Frame(nb)
        msg = f"Motor {M1.unit} is not available"
        mflag = 1
        message(M3.unit,mflag,msg)

    if M4.connected:
        page[4] = ttk.Frame(nb)
        B.tablet4()
        p4=M4.readMotor()
        if not p4:
            # put up a warning that M1 can't be read...
            print("Can't read unit ", M4.unit)
            msg = f"Motor {M1.unit} is not available"
            mflag = 1
            message(M4.unit,mflag,msg)
        else:
            I.setEntry(4, p4)
            grat2Pos = T.getRadioButn(4, tab4, page[4])
            grate2.set(grat2Pos)
    else:
        page[4] = ttk.Frame(nb)
        B.warntab(4)

#def update():

class MotorControl:
    """
	This class contains motor attributes and methods
	"""

    def __init__(self, unit, port, speed, position, resolution, zero, lower, upper):
        """
        :rtype: object
        """
        self.unit = unit
        self.port = port
        self.speed = speed
        self.position = position # current step position
        self.resolution = resolution
        self.zero = zero
        self.lower = lower
        self.upper = upper
        # make the correct object, don't try to connect
        self.client = ModbusClient(method='rtu')
        self.target = 0 # targeted step location
        self.connected = False

    def checkMotor(self):
        """
        Return true if the motor is connected and client is not a modbusioException,
        and true if we can read a register from the unit
        """
        read = 0

        if self.connected:
            if isinstance(self.client, ModbusException):
                print("checkMotor: Modbus ioexception for unit ", self.unit)
                return False
            # attempt to read a register - if we can't then we have a problem
            read = self.client.read_holding_registers(0x00D7, 1, unit=self.unit)
            if isinstance(read,  ModbusException):
                print("checkMotor: Modbus ioexception for unit ", self.unit)
                return False
            return True
        else:
            return False

    def closeMotor(self):
        """
		Close connection to motor unit

		:rtype: object
		:param unit:
		:return:
		"""
        try:
            self.client.close()
            if DBG:
                print("--- Close succeeded")
        except:
            if DBG:
                print("Can't close - null client!")
        return

    def connectMotor(self):
        """
		Connect to motor unit

		:rtype: object
		:param unit:
		:return client:
		"""
        res = 0
        if self.connected:
            return True

        port = port485
        unit = self.unit

        self.client = ModbusClient(method='rtu',
                            port=port,
                            retries=100,
                            timeout=0.5,
                            rtscts=True,
                            parity='E',
                            baudrate=9600,
                            strict=False,
                            stopbits=2,
                            unit=unit)
        if isinstance(self.client, ConnException):
            print("Connection error!")
            self.connected = False
            
        if DBG:
            print(".. connecting..")
        try:
            res = self.client.connect()
        except:
            res = 0
            print("Connection error!")

        if TEST:
            res = 1
            self.connected = True
            return True

        if res:
            self.connected = True
            if DBG:
                print("--- Connected ", unit)
            return True
        else:
            self.connected = False
            if DBG:
                print("--- Can't Connect ", unit)
            return False

    def jogMotor(self, delta):
        """
		Adjust motor position by delta.

		:param delta: correction for new motor position
		:return:
		"""
        global tk
        unit = self.unit
        speed = self.speed

        if DBG:
            print("jogMotor", unit, delta)
            print("CLIENT",unit,self.client)

        self.connectMotor()
        if self.outOfRange(delta):
            if DBG:
                print("JOG IS OUT OF RANGE RETURN")
            self.closeMotor()
            return
        
        #if self.checkMotor():
        #    self.chkAlrm()
            
        if self.checkMotor():
            cp = self.readMotor()
            jogPosition = int(delta) + cp
            self.client.write_register(0x7D, 0x20, unit=unit)
            self.client.write_register(0x0383, 1, unit=unit)
            self.client.write_register(0x1805, speed, unit=unit)
            if int(delta) > 0:
                self.client.write_register(0x7D, 0x1000, unit=unit)
                if DBG:
                    print("JOG MOTOR FWD",unit,"FROM",cp,"TO",jogPosition,"BY",int(delta))
            if int(delta) < 0:
                self.client.write_register(0x7D, 0x2000, unit=unit)
                if DBG:
                    print("JOG MOTOR REV",unit,"FROM",cp,"TO",jogPosition,"BY",int(delta))
            self.client.write_register(0x1803, jogPosition, unit=unit)
            self.client.write_register(0x7D, 0x8, unit=unit)
            rp = self.readDelay(jogPosition) 
            if unit > 20:
                self.client.write_register(0x7D, 0x8, unit=unit)
                self.client.write_register(0x7D, 0x20, unit=unit)
                self.client.write_register(0x7D, 0x0, unit=unit)
                self.client.write_register(0x1805, speed, unit=unit)
                self.client.write_register(0x1803, jogPosition - 10, unit=unit)
                self.client.write_register(0x7D, 0x8, unit=unit)
                rp = self.readDelay(jogPosition)
                self.client.write_register(0x7D, 0x8, unit=unit)
                self.client.write_register(0x7D, 0x20, unit=unit)
                self.client.write_register(0x7D, 0x0, unit=unit)
                self.client.write_register(0x1805, speed, unit=unit)
                self.client.write_register(0x1803, jogPosition, unit=unit)
                self.client.write_register(0x7D, 0x8, unit=unit)
                rp = self.readDelay(jogPosition)
            self.closeMotor()
            if DBG:
                print("jog to",rp)
            log.debug(rp)
            if rp == "None" or rp == "NoneType":
               pass
            # warn()
        else:
            rp = self.target
            jogPosition = int(delta) + rp
            mflag = 1
            msg = "Motor " + str(unit) +" is not available"
            print("!!! jogMotor has an ioException for unit ", self.unit)
            message(unit,mflag,msg)
            return

        if unit == 1:
            slidePos = T.getRadioButn(1, tab1, page[1])
            slide.set(slidePos)
        if unit == 2:
            cmparPos = T.getRadioButn(2, tab2, page[2])
            source.set(cmparPos)
        if unit == 3:
            grat1Pos = T.getRadioButn(3, tab3, page[3])
            grate1.set(grat1Pos)
        if unit == 4:
            grat2Pos = T.getRadioButn(4, tab4, page[4])
            grate2.set(grat2Pos)

        Location[unit] = rp
        I.setEntry(unit, rp)
        T.setLabel(unit, rp)

        self.position = rp
        if DBG:
            print("JogHERE",unit,jogPosition,"=",rp)
        if jogPosition != rp and self.client:
            if DBG:
                print("???????",jogPosition,rp)

    def outOfRange(self, delta):
            global tk
            unit = self.unit
            pos = self.position
            lower = self.lower
            upper = self.upper

            if DBG:
                print("POS:", pos)
            msg = str(pos + int(delta)) + " is Out of Range"
            flag = 0
            if pos + int(delta) < lower:
                flag = 1

            if pos + int(delta) > upper:
                flag = 2
                # potential side effect - why do this?
                Location[unit] = Upper[unit]
            if flag > 0:
                tk.Label(page[unit], font=20, foreground="#000000", text=msg).place(x=50, y=240, width=350, height=25)
            #else:
            #    tk.Label(page[unit], font=20, foreground="C0C0C0", text=msg).place(x=50, y=240, width=350, height=25)

            return flag
    
    def chkAlrm(self):
        read = 0

        if isinstance(self.client, ModbusException):
            return True

        if self.client and not TEST:
            read = self.client.read_holding_registers(0x007F, 1, unit=self.unit)
            alarm = read.registers[0] 
        else:
            alarm = 64
        if alarm == 64:
            self.readAlrm()
            self.connected = False
        else:
            return 

    def readAlrm(self):
        """
        Check for error of the 'unit' motor.

        :return: motor error status.
        """
        global _mode
        unit = self.unit

        if self.connectMotor() and not TEST:
            read = self.client.read_holding_registers(0x0081, 1, unit=unit)
            alarm = read.registers[0]
            self.closeMotor()
        else:
            alarm = 99
        

        b1 = tk.Button(main, text="Alarm", font=26, fg='red', bg='white', command=partial(self.seeAlrm, alarm), pady=2, height=30, width=70, relief='ridge')
        b1.place(x=10, y=30, width=70, height=30)
        return
        
    def seeAlrm(self, error):
        warn2 = "Motor " + str(self.unit) + " is NOT available."
        warn3 = "and shows error " + str(error) + "."
        warn4 = ""
### NEED A DICTIONARY FOR NESSAGES
        if error == 99:
            warn4 = "Motor driver is unreachable. Check power."
        temp = tk.Tk()
        temp.wm_title('ALARM')
        w = Canvas(temp, width=340, height=150)
        w.pack()
        w.create_text(170,15,text='ERROR:',font=20,fill="#FF0000")
        w.create_text(170,45,text=warn2,font=20)
        w.create_text(170,70,text=warn3,font=20)
        w.create_text(170,95,text=warn4,font=20)
        windowWidth = temp.winfo_reqwidth()
        windowHeight = temp.winfo_reqheight()
        positionRight = int(temp.winfo_screenwidth()/2 - windowWidth/1)
        positionDown = int(temp.winfo_screenheight()/2 - windowHeight/1)
        temp.geometry("+{}+{}".format(positionRight, positionDown))
        b = tk.Button(w, text='Okay', font=30, width=30, command = temp.destroy, anchor = S) 
        b.configure(width = 10, activebackground = "#BBBBBB")
        bw = w.create_window(120, 110, anchor=NW, window=b)
        b.place(x=120,y=110)
        temp.mainloop()
        temp.destroy

    def readDelay(self, target):
        """
        Loop on reading the motor position until
        the 'unit' motor gets to the target position.

        :param: target - motor destination position
        :return: motor position in user steps, -999 if error
        """

        global tk
        unit = self.unit
        client = self.client
        speed = self.speed

        read = client.read_holding_registers(0x00C7, 1, unit=unit)
        rp = read.registers[0]
        if DBG:
            print("readDelay IN",target,"pos",rp)
        delay = (abs(rp - target)) * 1.2 / speed
        ldelay = delay
        
        msg = "Wait " + str(int(10.0 * delay) / 10.0) + " sec"
        tk.Label(page[unit], font=20, foreground="#FF0000", text=msg).place(x=90, y=20, width=350, height=25)
        
        reps = 0
        speed = self.speed
        while (rp != target):
            reps += 1
            delay = (abs(rp - target))*1.2/speed
            if ldelay < delay:
                if DBG:
                    print("Motor going in wrong direction")
                self.client.write_register(0x7D, 0x20, unit=unit)
                self.client.write_register(0x7D, 0x0, unit=unit)
                break
            if ldelay == delay and reps == 5:
                if DBG:
                    print("Motor not going from",rp,"to",target)
                break
            
            if DBG:
                print("WAIT",delay,"sec to goto",target,"from",rp,"at", speed)
 
            ldelay = delay
            # set a busy cursor
            main.config(cursor="wait")
            main.update()
            sleep(delay)
            read = client.read_holding_registers(0x00C7, 1, unit=unit)
            rp = read.registers[0]
            main.config(cursor="")
            tk.Label(page[unit], font=20, foreground="#F0F0F0", text=msg).place(x=90, y=20, width=350, height=25)
            #e1 = tk.Label(page[unit], font=12, bg="#FFFFFF", text="WAIT", justify='right')
        if DBG:
            print("readDelay OUT",rp)
        self.position = rp
        return rp


    def readMotor(self):
        """
		Read the position of the 'unit' motor.

		:Return position or -999 if any exceptions
		"""
        global tk
        unit = self.unit
        position = self.position
        motorOK = False
        alarmOK = False

        if TEST:
            self.position = 1000
            return 1000

        # log.debug("READING REGISTER ")
        self.connectMotor()

        if self.checkMotor():
            read = self.client.read_holding_registers(0x00D7, 1, unit=unit)
            if isinstance(read, ModbusException):
                self.connected = False
                self.closeMotor()
                print("!!! Can't read registers from unit ", self.unit)
                # put up a warning message
                return -999
            
            #upprpos = read.registers[0]
            if DBG:
                print(f"Read motor {unit} Loc: {position} Pos: {self.position}")

            read = self.client.read_holding_registers(0x00C7, 1, unit=unit)
            log.debug(read)
            position = read.registers[0] 
            self.closeMotor()
        else:
            # warn()
            return -999

        self.position = position
    
        T.setLabel(unit, position)
        return position

    def getTarget(self):
        """
        Get value in data entry window.
        Send motor to that value
        """
        location = T.getLabel(self.unit)
        self.target = location
        self.sendMotor()
        if DBG2:
            print("GOT LOCATION",location)

    # major rework, now includes better exception handling
    def sendMotor(self):
        """
        Send the 'unit' motor to the target location.
        :return True if success, False otherwise (exception errors)
        """
        location = self.target
        unit = self.unit
        speed = self.speed
        if DBG:
            print("sendMotor", unit, location)

        self.connectMotor()

        if self.checkMotor():    
            if TEST:
                pos = 1000
            else:
                pos = self.readMotor()
        
            delta = location - pos
            if self.outOfRange(delta):
                if DBG:
                    print("SEND IS OUT OF RANGE. RETURN")
                self.closeMotor()
                return False

            setPosition = int(location) 
            if DBG2:
                print("SEND WRITE TRY ",unit," TO ",setPosition)
            self.client.write_register(0x7D, 0x20, unit=unit)
            self.client.write_register(0x1801, 1, unit=unit)
            self.client.write_register(0x0383, 1, unit=unit)
            self.client.write_register(0x1805, speed, unit=unit)
            if int(delta) > 0:
                if DBG:
                    print("SEND MOTOR FWD", unit, self.position)
            if int(delta) < 0:
                if DBG:
                    print("SEND MOTOR REV", unit, self.position)
            self.client.write_register(0x1803, setPosition, unit=unit)
            self.client.write_register(0x7D, 0x8, unit=unit)
            rp = self.readDelay(setPosition)
            if unit > 20:
                self.client.write_register(0x7D, 0x20, unit=unit)
                self.client.write_register(0x7D, 0x0, unit=unit)
                self.client.write_register(0x1801, 1, unit=unit)
                self.client.write_register(0x1805, speed, unit=unit)
                self.client.write_register(0x1803, setPosition - 10, unit=unit)
                self.client.write_register(0x7D, 0x8, unit=unit)
                rp = self.readDelay(setPosition)
                self.client.write_register(0x7D, 0x20, unit=unit)
                self.client.write_register(0x7D, 0x0, unit=unit)
                self.client.write_register(0x1801, 1, unit=unit)
                self.client.write_register(0x1805, speed, unit=unit)
                self.client.write_register(0x1803, setPosition, unit=unit)
                self.client.write_register(0x7D, 0x8, unit=unit)
                rp = self.readDelay(setPosition)
            self.closeMotor()
            if rp == "None" or rp == "NoneType":
                pass
                # warn()
        else:
            # we have an exception!
            mflag = 1
            msg = "Motor " + str(unit) +" is not available"
            print("!!! sendMotor has an ioException for unit ", self.unit)
            self.closeMotor
            message(unit,mflag,msg)
            return False

        Location[unit] = rp
        I.setEntry(unit, rp)
        T.setLabel(unit, rp)
       
        self.position = rp
        if DBG:
            print("WRITE",unit, self.position,"SPD",Speed[unit])
        return True

    def setMotor(self, tab):
        """
		Set the motor target position using the location for the selected RadioButton.

		:param tab: Tab number
		:return: None
		"""
        unit = self.unit
        if (unit == 1):
            location = [int(i[2]) for i in tab1][slide.get()]
        if (unit == 2):
            location = [int(i[2]) for i in tab2][source.get()]
        if (unit == 3):
            location = [int(i[2]) for i in tab3][grate1.get()]
        if (unit == 4):
            location = [int(i[2]) for i in tab4][grate2.get()]
        self.target = location

        if DBG:
            print("SET MOTOR TARGET",unit,location,tab,source.get(),slide.get())
        # TODO: error trapping here
        self.sendMotor()
    
    def stopMotor(self):
        """
		Stop the motor

		:param unit: motor index number,
		:param tab: Tab number
		:return: None
		"""
        if self.checkMotor():
            self.client.write_register(0x7D, 0x20, unit=self.unit)
            self.client.write_register(0x7D, 0x0, unit=self.unit)
        else:
            print("Can't stop motor - client ioException error")


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
        val = str(var.get())

        if not val:
            return
  
        if DBG2:
            print("CALLBACK",t,val)
        try:
            int(val)
        except:
            filter_char = lambda char: char.isdigit()
            val = filter(filter_char, val)
            if val.find("-") > 0:
                val = val.replace("-","")
            try:
                int(val)
            except:
                return False

        if int(val) < 0:
            val = "0"
        if int(val) > Upper[t]:
            val = str(Upper[t])
        var.set(val)

        self.setAngle(val, t, x, y)

        return True


    def convertL2S(self, lstr):
        # initialization of string to ""
        new = ""

        # convert first level list to string
        #s = [item for sublist in l for item in sublist]
        s = [str(i) for i in lstr]

        # traverse each list
        for line in s:
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

    def convertS2Dms(self, val, res):
        # convert a step value to degrees, minutes, seconds

        dg = float(int(val)) * 360.0 / float(res)
        di = int(dg)
        mn = (dg - float(di)) * 60.0
        mi = int(mn)
        sc = (mn - float(mi)) * 60.0
        si = int(sc)
        if di == 0:
            st = str(abs(mi)) + "'" + str(abs(si)) + '"'
        else:
            st = str(di) + u"\u00b0" + str(abs(mi)) + "'" + str(abs(si)) + '"'
        if val < 0:
            st = "-" + st
        return st

    def convertS2Dcd(self, val, res):
        # convert a step value to decimal degrees

        dg = float(int(val)) * 360.0 / float(res)
        st =str(dg)
        if val < 0:
            st = "-" + st
        return st


    def convertS2   (self, val, res):
        # convert a step value to degrees, decimal minutes

        dg = float(int(val)) * 360.0 / float(res)
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

        if val < 0:
            st = "-" + st
        return st

    def initEntry(self, unit):
        rp = Location[unit]
        strv = tk.StringVar()
        strv.set(rp)

    def setAngle(self, val, t, x, y):
            """
            Display the motor angle
            """
            if t > 2:
                loc = Location[t] - Reference[t]
                st = I.convertS2Dcd(loc, Resolution[t])
                str1 = tk.StringVar()
                str1.set(str(loc))
                str1.trace("w", lambda name, index, mode, sv=str1: I.callback(str1, t, 205, 145))
            # ANGLE DISPLAY WINDOW. "Label" sets x, y
                e1 = tk.Label(page[t], font=12, bg="#FFFFFF", text=st, justify='right')
                e1.place(x=x, y=y-50, width=80, height=20)


    def is_number(self, var):
        """
        Test whether variable is a number.

        :param var:
        :return: True/False
        """
        try:
            if var == int(var):
                return True
        except Exception:
            return False


    def setEntry(self, t, val):
        """
        Get Entry values.

        :param t: tab number
        :param val: enter value
        :return:
        """
        global e

        val = str(int(val))
        if DBG2:
            print("SETENTRY target location", t, "VAL", val)

        if t < 3:
            strv = tk.StringVar()
            strv.set(str(val))
            strv.trace("w", lambda name, index, mode, sv=strv: I.callback(strv, t, 215, 105))
            e[t] = tk.Entry(page[t], font=12, textvariable=strv, bg="#FFFFFF", validate="focusout",
                            validatecommand=I.callback(strv, t, 215, 105), justify='right')
            e[t].place(x=245, y=175, width=60, height=20)
        if t > 2:
            str1 = tk.StringVar()
            str1.set(str(val))
            str1.trace("w", lambda name, index, mode, sv=str1: I.callback(str1, t, 200, 100))
            e[t] = tk.Entry(page[t], font=12, textvariable=str1, bg="#FFFFFF", validate="focusout",
                            validatecommand=I.callback(str1, t, 200, 100), justify='right')
            e[t].place(x=210, y=195, width=60, height=20)



class LocalIO:
    """

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
        global pos1, pos2, pos3, pos4
        global tmp1, tmp2, tmp3, tmp4

        filename = DFLT_POSIX
        fileHandle = open(filename, "r")
        records = fileHandle.readlines()
        fileHandle.close()

        for record in records:
            line = record.split()
            if line[1] == 'jog':
                if line[0] == str(1):
                    jog1.append(line)
                if line[0] == str(2):
                    jog2.append(line)
                if line[0] == str(3):
                    jog3.append(line)
                if line[0] == str(4):
                    jog4.append(line)
            else:
                if line[1] != 'res' and line[1] != 'ref':
                    if line[0] == str(1):
                        tab1.append(line)
                    if line[0] == str(2):
                        tab2.append(line)
                    if line[0] == str(3):
                        tab3.append(line)
                    if line[0] == str(4):
                        tab4.append(line)
                if line[1] == 'ref':
                    if line[0] == str(1):
                        Reference[1] = int(line[2])
                    if line[0] == str(2):
                        Reference[2] = int(line[2])
                    if line[0] == str(3):
                        Reference[3] = int(line[2])
                    if line[0] == str(4):
                        Reference[4] = int(line[2])

        pos1 = tab1
        pos2 = tab2
        pos3 = tab3
        pos4 = tab4
        tmp1 = copy.deepcopy(tab1)
        tmp2 = copy.deepcopy(tab2)
        tmp3 = copy.deepcopy(tab3)
        tmp4 = copy.deepcopy(tab4)

        if DBG:
            print(filename)
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

        fileHandle = open(CONFIG_FILENAME,"r")
        records = fileHandle.readlines()
        fileHandle.close()
        record = 0
        line = ''

        for record in records:
            line = record.split()
            count = len(line)
            if line[0] == '1':
                Offset[1] = int(line[2])
                Zero[1] = int(line[3])
                Speed[1] = int(line[4])
            if line[0] == '2':
                Offset[2] = int(line[2])
                Zero[2] = int(line[3])
                Speed[2] = int(line[4])
            if line[0] == '3':
                Offset[3] = int(line[2])
                Zero[3] = int(line[3])
                Speed[3] = int(line[4])
            if line[0] == '4':
                Offset[4] = int(line[2])
                Zero[4] = int(line[3])
                Speed[4] = int(line[4])

    def readUser(self):
        """
        Read user tablet settings.
         .
        :return: selected filename
        """
        filename = askopenfilename(initialdir="./", title="Select file",
                                   filetypes=(("config files", "*.usr"), ("all files", "*.*")))

        # global pos1, pos2, pos3, pos4
        # item1, item2, item3, item4 = 0
        global tab1, tab2, tab3, tab4
        global tmp1, tmp2, tmp3, tmp4
        global pos1, pos2, pos3, pos4

        # read whole file
        fileHandle = open(filename, "r")
        records = fileHandle.readlines()
        fileHandle.close()

        #init_cfg()
        del tab1[:]
        del tab2[:]
        del tab3[:]
        del tab4[:]
        del tmp1[:]
        del tmp2[:]
        del tmp3[:]
        del tmp4[:]

        # parse records into tabs
        for record in records:
            line = record.split()
            count = len(line)

            if line[1] == 'jog':
                if line[0] == str(1):
                    jog1.append(line)
                if line[0] == str(2):
                    jog2.append(line)
                if line[0] == str(3):
                    jog3.append(line)
                if line[0] == str(4):
                    jog4.append(line)
            else:
                if line[1] != 'res' and line[1] != 'ref':
                    if line[0] == str(1):
                        tmp1.append(line)
                    if line[0] == str(2):
                        tmp2.append(line)
                    if line[0] == str(3):
                        tmp3.append(line)
                    if line[0] == str(4):
                        tmp4.append(line)
                if line[1] == 'ref':
                    if line[0] == str(1):
                        Reference[1] = int(line[2])
                    if line[0] == str(2):
                        Reference[2] = int(line[2])
                    if line[0] == str(3):
                        Reference[3] = int(line[2])
                    if line[0] == str(4):
                        Reference[4] = int(line[2])

        pos1 = tmp1
        pos2 = tmp2
        pos3 = tmp3
        pos4 = tmp4
        tab1 = copy.deepcopy(tmp1)
        tab2 = copy.deepcopy(tmp2)
        tab3 = copy.deepcopy(tmp3)
        tab4 = copy.deepcopy(tmp4)
        if DBG:
            print("USER ",tab2)
        filename = path.basename(filename)
        main.title('GAP Motor Control: using ' + str(filename))
        main.title('USER settings: ' + str(filename))
        if DBG:
            print(filename)
        #update()

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

    def chkPassword(self, root, pw):
        """
        Verify password
        """
        if pw.get() == 'abc123' or pw.get() == 'OOS39023' or pw.get() == '123abc':
            try:
                root.destroy()
                F.setConfig()
            except:
                pass
        else:
            pass

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

        tk.Label(pw, font=20, text="Password").grid(row=1, column=1)
        rs = tk.StringVar()
        rs = tk.Entry(pw, font=20, width=10, justify=RIGHT, borderwidth=2)
        rs.grid(row=1, column=3)
        b1 = tk.Button(pw, text="Enter", font=20, command=partial(F.chkPassword, pswd, rs), pady=2, height=0, width=4, relief='ridge')
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
        hdr5 = "\toffset \tzero \tspeed \n"
        str1 = I.convertL2S(o[1]) + "\t" + I.convertL2S(z[1]) + "\t" + I.convertL2S(s[1]) + "\n"
        str2 = I.convertL2S(o[2]) + "\t" + I.convertL2S(z[2]) + "\t" + I.convertL2S(s[2]) + "\n"
        str3 = I.convertL2S(o[3]) + "\t" + I.convertL2S(z[3]) + "\t" + I.convertL2S(s[3]) + "\n"
        str4 = I.convertL2S(o[4]) + "\t" + I.convertL2S(z[4]) + "\t" + I.convertL2S(s[4]) + "\n"

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
        fileHandle = open(filename,"w")
        fileHandle.writelines(records)
        fileHandle.close()

        if DBG:
            print("wrote",filename)

        # reset current values
        for i in range(5):
            if i == 0:
                continue
            Offset[i] = int(o[i].get())
            Zero[i] = int(z[i].get())
            Speed[i] = int(s[i].get())

        win.destroy()

    def setConfig(self):
        """

        :return:
        """
        conf = tk.Tk()
        conf.wm_title('Settings')
        page[0] = Canvas(conf, width=850, height=280)
        #page[0].grid()
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
        z[1].insert(0, Zero[1])
        z[2].insert(0, Zero[2])
        z[3].insert(0, Zero[3])
        z[4].insert(0, Zero[4])
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
        o[1].insert(0, Offset[1])
        o[2].insert(0, Offset[2])
        o[3].insert(0, Offset[3])
        o[4].insert(0, Offset[4])
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
        #     tk.Label(conf, font=20, foreground="C0C0C0", text=msg).place(x=100, y=240, width=350, height=25)
        s[2] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        s[3] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        s[4] = tk.Entry(page[0], width=8, justify=RIGHT, borderwidth=2)
        s[1].insert(0, Speed[1])
        s[2].insert(0, Speed[2])
        s[3].insert(0, Speed[3])
        s[4].insert(0, Speed[4])
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
        u[1].insert(0, Upper[1])
        u[2].insert(0, Upper[2])
        u[3].insert(0, Upper[3])
        u[4].insert(0, Upper[4])
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

    """
    def getLabel(self, t):
        """
        Get the entered value.

        :param unit: motor index number
        :return: Entry value
        """
        global e

        s = e[t].get()
        if s == '':
            s = 0
        return int(s)

    def getRadioButn(self, unit, tablist, page):
        """
        Gets the RadioButton that matches the motor position.

        :param unit: motor index number
        :param tablist: contents array for the selected tablet
        :param page: associated page number for the tablist
        :return: the RadioButton number found
        """

        if unit == 1:
            position = M1.readMotor()
            closest = T.getClosest(unit, position, tab1)
            tmp1[closest][2] = position
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
            print("GET Radio --- ",unit,closest,position)
        return closest

    def getClosest(self, unit, position, tablist):
        """
        Gets the RadioButton that matches the motor position.

        :param unit: motor index number
        :param tablist: contents array for the selected tablet
        :param page: associated page number for the tablist
        :return: the RadioButton number found
        """

        global _warn1

        if DBG2:
            print(tablist)

        list_of_numbers = [int(i[2]) for i in tablist]
         closest = min(enumerate(list_of_numbers), key=lambda ix: (abs(ix[1] - position)))[0]
        # nearest = list_of_numbers[closest]
        # difference = position - nearest
        '''
        if abs(difference) > 0 and unit < 3:
            message = "Motor " + str(unit) + " at " + str(position) + " is off " + str(difference) + " steps from " + str(nearest) + ". Re-click selection."
            tk.Label(page[unit], font=20, foreground="#EE0000", text=message).place(x=50, y=240, width=450, height=25)
            _warn1 = message
        elif unit < 3:
            tk.Label(page[unit], font=20, foreground="#F0F0F0", text=_warn1).place(x=50, y=240, width=450, height=25)
            _warn = ""
        #return closest

        if abs(difference) > 0:
            message = "Notice: Motor is off " + str(difference) + " steps. Click selection."
            _warn1 = message
        '''
    
        return closest

    def resetTab(self):
        """
        Reset settings to the llast file opened.

        :return: None
        """
        global pos1, pos2, pos3, pos4
        pos1 = tab1
        pos2 = tab2
        pos3 = tab3
        pos4 = tab4

    def setLabel(self, t, position, x=215, y=105):
        """
        Display the motor position
        """
        global e1

        try:
            if t < 3:
                e1 = tk.Label(page[t], font=12, bg="#FFFFFF", text=position, justify='right')
                e1.place(x=x + 20, y=y, width=60, height=20)
            if t > 2:
                e1 = tk.Label(page[t], font=12, bg="#FFFFFF", text=position, justify='right')
                e1.place(x=x - 5, y=y + 20, width=60, height=20)
                #e1.place(x=210, y=195, width=60, height=20)
        except:
            return

    def setLimits (self):
        """
        Toggle show/hide limits
        """

        global limitSet

        if limitSet == 'Show':
            limitSet = 'Hide'
        else:
            limitSet = 'Show'
        filemenu.entryconfig(2,label=limitSet + " Limits")

    def updateTabLocations(self):
        """

        :param unit:
        :return:
        """
        global pos1, pos2, pos3, pos4

        for unit in range(1,5):
            if (unit == 1):
                tablist = tab1
            if (unit == 2):
                tablist = tab2
            if (unit == 3):
                tablist = tab3
            if (unit == 4):
                tablist = tab4
            tabN = []
            n = 1
            for i in tablist:
                i[2] = Location[unit][n]
                tabN.append(i)
                n+=1
            if (unit == 1):
                pos1 = tabN
            if (unit == 2):
                pos2 = tabN
            if (unit == 3):
                pos3 = tabN
            if (unit == 4):
                pos4 = tabN



class MakeTab:
    '''
    '''
    def _init_(self, unit):
        self.unit = unit


    def tablet1(self):
        """
        Display tablet 1 for motor number 'unit'.

        :param unit: motor index number.
        :return:
        """
        global Resolution

        nb.add(page[1], text="Slide", sticky='NESW')

        jogN = len(jog1); jogR = jogN * 20; jogS = 110 - jogR / 4

        tk.Label(page[1], font=20, text="Current location").place(x=190, y=70, width=150, height=25)
        tk.Label(page[1], font=20, text="Enter new location").place(x=190, y=140, width=150, height=25)
        tk.Label(page[1], font=20, text="Jog").place(x=350, y=jogS, width=150, height=25)

        row = 0
        for line in tab1:
            if line[1] != 'tab' and line[1] != 'res' and line[1] != 'ref':
                if len(line) == 5:
                    name = line[3] + " " + line[4]
                else:
                    name = line[3]
                butn="rb" + str(row)
                butn = tk.Radiobutton(page[1], font=20, text=name, command=partial(M1.setMotor, 1), padx=20,
                           variable=slide, value=row, anchor='w').place(x=20, y=jogS+20+20*row, width=150, height=25)
                row = row + 1

        row1 = 0; row2 = 0
        for line in jog1:
            if line[1] == 'jog':
                if int(line[2]) < 0:
                    ##print(line[2])
                    tk.Button(page[1], font=12, text=line[3], command=partial(M1.jogMotor, line[2]), padx=40,
                          relief='ridge').place(x=380, y=jogS+30+row1*20, width=50, height=22)
                    row1 = row1 + 1
                if int(line[2]) > 0:
                    tk.Button(page[1], font=12, text=line[3], command=partial(M1.jogMotor, line[2]), padx=40,
                          relief='ridge').place(x=428, y=jogS+30+row2*20, width=50, height=22)
                    row2 = row2 + 1

        tk.Button(page[1], font=20, text="Go", command=partial(M1.getTarget), padx=40).place(x=215, y=175, width=30, height=20)

    def tablet2(self):
        """
        Display tablet 2 for motor number 'unit'.

        :param unit: motor index number.
        :return:
        """
        global Resolution

        nb.add(page[2], text="Comparisons", sticky='NESW')

        jogN = len(jog2); jogR = jogN * 20; jogS = 110 - jogR / 4

        tk.Label(page[2], font=20, text="Current location").place(x=190, y=70, width=150, height=25)
        tk.Label(page[2], font=20, text="Enter new location").place(x=190, y=140, width=150, height=25)
        tk.Label(page[2], font=20, text="Jog").place(x=350, y=jogS, width=150, height=25)

        row = 0
        for line in tab2:
            if line[1] != 'tab' and line[1] != 'res' and line[1] != 'ref':
                if len(line) == 5:
                    name = line[3] + " " + line[4]
                else:
                    name = line[3]
                tk.Radiobutton(page[2], font=20, text=name, command=partial(M2.setMotor, 2), padx=20,
                           variable=source, value=row, anchor='w').place(x=20, y=jogS+25+20*row, width=150, height=25)
                row = row + 1

        row1 = 0; row2 = 0
        for line in jog2:
            if line[1] == 'jog':
                if int(line[2]) < 0:
                    tk.Button(page[2], font=12, text=line[3], command=partial(M2.jogMotor, line[2]), padx=40,
                          relief='ridge').place(x=380, y=jogS+30+row1*20, width=50, height=22)
                    row1 = row1 + 1
                if int(line[2]) > 0:
                    tk.Button(page[2], font=12, text=line[3], command=partial(M2.jogMotor, line[2]), padx=40,
                          relief='ridge').place(x=428, y=jogS+30+row2*20, width=50, height=22)
                    row2 = row2 + 1
 
        tk.Button(page[2], font=20, text="Go", command=partial(M2.getTarget), padx=40).place(x=215, y=175, width=30, height=20)

    def tablet3(self):
        """
        Display tablet 3 for motor number 'unit'.

        :param unit: motor index number.
        :return:
        """
        global Resolution, Reference

        nb.add(page[3], text="Grating 1", sticky='NESW')

        jogN = len(jog3); jogR = jogN * 20; jogS = 110 - jogR / 4

        tk.Label(page[3], font=20, text="Grating 1 angle is").place(x=30, y=50, width=150, height=25)
        tk.Label(page[3], font=20, text="Current location").place(x=30, y=120, width=150, height=25)
        tk.Label(page[3], font=20, text="Enter new location").place(x=30, y=190, width=150, height=25)
        tk.Label(page[3], font=20, text="Jog").place(x=350, y=jogS, width=150, height=25)
        tk.Label(page[3], font=10, text="2500 steps per 9" + u"\u00b0").place(x=-10, y=215, width=250, height=25)

        row = 0
        for line in tab3:
            if line[1] != 'tab' and line[1] != 'res' and line[1] != 'ref':
                if len(line) == 5:
                    name = line[3] + " " + line[4]
                else:
                    name = line[3]
                tk.Radiobutton(page[3], font=20, text=name, command=partial(M3.setMotor, 3), padx=20,
                           variable=grate1, value=row, anchor='w').place(x=20, y=75+20*row, width=150, height=25)
                row = row + 1
            if line[1] == 'res':
                Resolution[t] = int(line[2])
                #_res.append[res[t])
            if line[1] == 'ref':
                Reference[t] = int(line[2])
                #_ref[unit] = int(line[2])

        row1 = 0; row2 = 0
        for line in jog3:
            if line[1] == 'jog':
                if int(line[2]) < 0:
                    tk.Button(page[3], font=12, text=line[3], command=partial(M3.jogMotor, line[2]), padx=40,
                          relief='ridge').place(x=380, y=jogS+30+row1*20, width=50, height=22)
                    row1 = row1 + 1
                if int(line[2]) > 0:
                    tk.Button(page[3], font=12, text=line[3], command=partial(M3.jogMotor, line[2]), padx=40,
                          relief='ridge').place(x=428, y=jogS+30+row2*20, width=50, height=22)
                    #st = I.convertS2Dcd(line[3], res[3])
                    #tk.Label(page[3], font=12, text=st).place(x=476, y=jogS+30+row2*20, width=50, height=22)
                    row2 = row2 + 1

        tk.Button(page[3], font=20, text="Go", fg="red", command=partial(M3.getTarget), padx=40).place(x=225, y=160, width=30, height=20)

    def tablet4(self):
        """
        Display tablet 4 for motor number 'unit'.

        :param unit: motor index number.
        :return:
        """
        global Resolution, Reference

        nb.add(page[4], text="Grating 2", sticky='NESW')

        jogN = len(jog4); jogR = jogN * 20; jogS = 110 - jogR / 4

        tk.Label(page[4], font=20, text="Grating 2 angle is").place(x=30, y=50, width=150, height=25)
        tk.Label(page[4], font=20, text="Current location").place(x=30, y=120, width=150, height=25)
        tk.Label(page[4], font=20, text="Enter new location").place(x=30, y=190, width=150, height=25)
        tk.Label(page[4], font=20, text="Jog").place(x=350, y=jogS, width=150, height=25)
        tk.Label(page[4], font=10, text="2500 steps per 9" + u"\u00b0").place(x=-10, y=215, width=250, height=25)

        row = 0
        for line in tab4:
            if line[1] != 'tab' and line[1] != 'res' and line[1] != 'ref':
                if len(line) == 5:
                    name = line[3] + " " + line[4]
                else:
                    name = line[3]
                tk.Radiobutton(page[4], font=20, text=name, command=partial(M4.setMotor, 4), padx=20,
                           variable=grate2, value=row, anchor='w').place(x=20, y=75+20*row, width=150, height=25)
                row = row + 1
            if line[1] == 'res':
                Resolution[t] = int(line[2])
            if line[1] == 'ref':
                Reference[t] = int(line[2])

        row1 = 0; row2 = 0
        for line in jog4:
            if line[1] == 'jog':
                if int(line[2]) < 0:
                    tk.Button(page[4], font=12, text=line[3], command=partial(M4.jogMotor, line[2]), padx=40,
                          relief='ridge').place(x=380, y=jogS+30+row1*20, width=50, height=22)
                    row1 = row1 + 1
                if int(line[2]) > 0:
                    tk.Button(page[4], font=12, text=line[3], command=partial(M4.jogMotor, line[2]), padx=40,
                          relief='ridge').place(x=428, y=jogS+30+row2*20, width=50, height=22)
                    row2 = row2 + 1

        tk.Button(page[4], font=20, text="Go", fg="red", command=partial(M4.getTarget), padx=40).place(x=225, y=160, width=30, height=20)

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
        tk.Label(page[unit], font=20, text=warn2, bg="#FFCCCC").place(x=90, y=90, width=350, height=25)
        tk.Label(page[unit], font=20, text=warn3, bg="#FFCCCC").place(x=90, y=120, width=350, height=25)
        tk.Label(page[unit], font=20, text=warn4, bg="#FFCCCC").place(x=90, y=150, width=350, height=25)
        tk.Label(page[unit], font=20, text=warn5, bg="#FFCCCC").place(x=90, y=180, width=350, height=25)

"""
Main loop, initialize.
"""
#global variables

# discover com port to RS485
print("PORTS",ports)
i = 0
for p,q,r in ports:
    i += 1
    if r.find("FTDIBUS") >= 0:
        print("RS485","P",p,"Q",q,"R",r)
        port485=p
    else:
        print("MOTOR",i,"port",p)

port485="COM6"

"""
Motor check.
"""
F = LocalIO()
F.readConfig()


# do full initialization of the object. no global vars.
M1 = MotorControl(1, "com7", 100,   0, 1000,   3000, 0, 8000)
M2 = MotorControl(2, "com8", 100,   0, 1000,      0, 0, 1000)
M3 = MotorControl(3, "com9", 10000, 0, 100000, 1000, 0, 12500)
M4 = MotorControl(4, "com3", 10000, 0, 100000, 1000, 0, 150000)
M1.connectMotor()
M1.closeMotor()
M2.connectMotor()
M2.closeMotor()
M3.connectMotor()
M3.closeMotor()
M4.connectMotor()
M4.closeMotor()
if not TEST and not M1.connected and not M2.connected and not M3.connected and not M4.connected:
        warn()
        exit()


"""
Main loop, begin.
"""
main = tk.Tk()
main.wm_title('GAP Motor Control')
main.geometry('550x300')
menubar = tk.Menu(main)

# Gets the requested values of the height and widht.
windowWidth = main.winfo_reqwidth()
windowHeight = main.winfo_reqheight()
#print("Width",windowWidth,"Height",windowHeight)
 
# Gets both half the screen width/height and window width/height
positionRight = int(main.winfo_screenwidth()/2 - windowWidth/1)
positionDown = int(main.winfo_screenheight()/2 - windowHeight/1)
 
# Positions the window in the center of the page.
main.geometry("+{}+{}".format(positionRight, positionDown))

# display the menu
main.config(menu=menubar)

B = MakeTab()
I = InputControl()
T = TabControl()
#print("START INITIALIZE")

#_warn2 = '' ### COMMENT THIS LINE WHEN MOTORS ARE AVAILABLE
#if _mode == 1:
#    warn(unit, 1646)

# Global variables
strv = tk.StringVar()
str1 = tk.StringVar()
str2 = tk.StringVar()

fname = F.readDflt()

slide = tk.IntVar()
source = tk.IntVar()
grate1 = tk.IntVar()
grate2 = tk.IntVar()

menu()

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
# myLabel.pack()
main.mainloop()
"""
End main loop
"""
