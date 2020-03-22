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
TEST = 1

mflag = 0
Resolution = [0,1000,1000,100000,100000]
Reference = [0,0,0,0,0]
Speed = [0, 100, 100, 10000, 10000]
Location = [0, 0, 0, 0, 0]; # array of user coordinates
Upper = [0, 8000, 1000, 12500, 150000]
Lower = [0, 0, 0, 0, 0]
Offset = [0, 8000, 1000, 15000, 15000]
Zero = [0, 3000, 0, 1000, 1000]
Offset = [0, 0, 0, 0, 0]
Zero = [0, 0, 0, 0, 0]

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
for p,q,r in ports:
    if "USB" in q:
        continue
    #com = int(filter(str.isdigit, p))
    com = filter(str.isdigit, p)
    print("P",p,com)

PATH = pathlib.Path(__file__).parent.joinpath("").resolve()
CONFIG_FILENAME = "GAPMC.ozs"
CONFIG_PATH = PATH.joinpath(CONFIG_FILENAME)
CONFIG_POSIX = CONFIG_PATH.as_posix()
#CONFIG_POSIX = path.basename(CONFIG_FILENAME)

DFLT_FILENAME = "GAPMC.dft"
DFLT_PATH = PATH.joinpath(DFLT_FILENAME)
DFLT_POSIX = DFLT_PATH.as_posix()
#DFLT_POSIX = path.basename(DFLT_FILENAME)

print(CONFIG_POSIX)
print(DFLT_POSIX)

#exit()


def exit():
    """
    Provides a single exit point.

    Will test for changes and ask if changes should be saved.

    return:
    """
    sys.exit()
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
        print(unit,"MESSAGE:",msg,">",page[unit-1],"<")
        l = tk.Label(main, font=20, foreground="#000000", text=msg).place(x=100, y=50, width=350, height=25)
        mflag = 0
    else:
        print(unit,"BLANK MESSAGE")
        l = tk.Label(main, font=20, foreground="#F0F0F0", text=msg).place(x=100, y=50, width=350, height=25)


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
    temp.geometry("+{}+{}".format(positionRight, positionDown))
    b = tk.Button(w, text='QUIT', font=30, width=35, command = exit, anchor = S) 
    b.configure(width = 10, activebackground = "#BBBBBB")
    bw = w.create_window(120, 110, anchor=NW, window=b)
    b.place(x=120,y=110)
    temp.mainloop()
    temp.destroy
    exit()

def run():
    global nb
    if M1.connected:
        page[1] = ttk.Frame(nb)
        item1 = B.tablet1()
        p1=M1.readMotor()
        I.setEntry(1, p1)
        slidePos = T.getRadioButn(1, tab1, page[1])
        slide.set(slidePos)
    else:
        page[1] = ttk.Frame(nb)
        item1 = B.warntab(1)
    if M2.connected:
        page[2] = ttk.Frame(nb)
        item2 = B.tablet2()
        p2=M2.readMotor()
        I.setEntry(2 ,p2)
        cmparPos = T.getRadioButn(2, tab2, page[2])
        source.set(cmparPos)
    else:
        page[2] = ttk.Frame(nb)
        item2 = B.warntab(2)
    if M3.connected:
        page[3] = ttk.Frame(nb)
        item3 = B.tablet3()
        p3=M3.readMotor()
        I.setEntry(3, p3)
        grat1Pos = T.getRadioButn(3, tab3, page[3])
        grate1.set(grat1Pos)
    else:
        page[3] = ttk.Frame(nb)
        item3 = B.warntab(3)
    if M4.connected:
        page[4] = ttk.Frame(nb)
        item4 = B.tablet4()
        p4=M4.readMotor()
        I.setEntry(4, p4)
        grat2Pos = T.getRadioButn(4, tab4, page[4])
        grate2.set(grat2Pos)
    else:
        page[4] = ttk.Frame(nb)
        item4 = B.warntab(4)

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
        self.position = position
        self.resolution = resolution
        self.zero = zero
        self.lower = lower
        self.upper = upper
        self.client = 0
        self.location = 0
        self.connected = False

    def closeMotor(self):
        """
		Close connection to motor unit

		:rtype: object
		:param unit:
		:return:
		"""
        try:
            self.client.close()
            print("CLOSE succeeded")
        except:
            print("Can't close - null client!")
        return

    def connectMotor(self):
        """
		Connect to motor unit

		:rtype: object
		:param unit:
		:return client:
		"""
        if self.connected:
            return True
        # we should really use the
        port = self.port

        try:
            # we should really use self.port for port here... -egs-
            # but we need to set it by reading the actual COM port #
            self.client = ModbusClient(method='rtu',
                              port=port485,
                              retries=1000,
                              timeout=0.4,
                              rtscts=True,
                              parity='E',
                              baudrate=9600,
                              unit=self.unit)

            res = self.client.connect()
        except:
            res = 0

        if TEST and self.unit != 0:
            res = 1
            self.client = False
            self.connected = False
        if res:
            self.connected = True
            return True
        else:
            self.connected = False
            return False


    def jogMotor(self, delta):
        """
		Adjust motor delta.

		:param unit: motor index number
		:param position: new motor position for delta
		:return:
		"""
        global tk
        unit = self.unit
        client = self.client

        print("")
        print("jogMotor", unit, delta)
        print("CLIENT",unit,self.client)
        if client and I.outOfRange(unit, delta) > 0:
            #print("JOG IS OUT OF RANGE RETURN")
            return
        # we don't need try/except since we are not throwing exceptions!
        if client:
            cp = self.readMotor()
            jogPosition = int(delta) + cp
            client.write_register(0x7D, 0x20, unit=unit)
            client.write_register(0x0383, 1, unit=unit)
            client.write_register(0x1805, int(Speed[unit]), unit=unit)
            if int(delta) > 0:
                client.write_register(0x7D, 0x1000, unit=unit)
                print("JOG MOTOR FWD",unit,"FROM",cp,"TO",jogPosition,"BY",int(delta))
            if int(delta) < 0:
                client.write_register(0x7D, 0x2000, unit=unit)
                print("JOG MOTOR REV",unit,"FROM",cp,"TO",jogPosition,"BY",int(delta))
            client.write_register(0x1803, jogPosition, unit=unit)
            client.write_register(0x7D, 0x8, unit=unit)
            rp = self.readDelay(jogPosition) 
            if unit > 20:
                client.write_register(0x7D, 0x8, unit=unit)
                client.write_register(0x7D, 0x20, unit=unit)
                client.write_register(0x7D, 0x0, unit=unit)
                client.write_register(0x1805, int(Speed[unit]), unit=unit)
                client.write_register(0x1803, jogPosition - 10, unit=unit)
                client.write_register(0x7D, 0x8, unit=unit)
                rp = self.readDelay(jogPosition)
                client.write_register(0x7D, 0x8, unit=unit)
                client.write_register(0x7D, 0x20, unit=unit)
                client.write_register(0x7D, 0x0, unit=unit)
                client.write_register(0x1805, int(Speed[unit]), unit=unit)
                client.write_register(0x1803, jogPosition, unit=unit)
                client.write_register(0x7D, 0x8, unit=unit)
                rp = self.readDelay(jogPosition)
            self.closeMotor(client)
            #print("jog to",rp)
            log.debug(rp)
            if rp == "None" or rp == "NoneType":
                warn(unit, 292)
        else:
            rp = self.location
            jogPosition = int(delta) + rp
            mflag = 1
            msg = "Motor " + str(unit) +" is not available"
            print("HERE???")
            message(unit,mflag,msg)

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

        I.setEntry(unit, rp)
        T.setLabel(unit, rp)
        #Location[unit] = rp
        self.location = rp
        print("JogHERE",unit,jogPosition,"=",rp)
        if jogPosition != rp and client:
            print("?????????????????????????????????????????????????????????????????????",jogPosition,rp)
            #client.write_register(903, 0, unit=unit)
        #print("")

    def readAlrm(self):
        """
        Read the position of the 'unit' motor.

        :param unit: motor index number
        :return: motor position in steps.
        """
        global _mode
        unit = self.unit

        client = self.client
        if client:
            read = client.read_holding_registers(0x0080, 1, unit=unit)
            upprpos = read.registers[0]
            read = client.read_holding_registers(0x0081, 1, unit=unit)
            self.closeMotor(client)
            log.debug(read)
            alarm = read.registers[0]
            self.closeMotor()
            # #print("motor",unit,"at",position,"upper",upprpos)
        else:
            #_mode = 1
            return

        #print("Motor",unit,"ALARM",alarm)
        return alarm

    def readDelay(self, position):
        """
        Loop on reading the position until
        the 'unit' motor get there.

        :param unit: motor index number
        :return: motor position in user steps.
        """
        #return position
        global tk
        unit = self.unit
        client = self.client

        read = client.read_holding_registers(0x00C7, 1, unit=unit)
        rp = read.registers[0]
        print("readDelay IN",position,"pos",rp)
        delay = (abs(rp - position)) * 1.2 / Speed[unit]
        ldelay = delay
        #msg = "Wait " + str(int(10.0 * delay) / 10.0) + " sec"
        #tk.Label(page[unit], font=20, foreground="#000000", text=msg).place(x=50, y=240, width=350, height=25)
        reps = 0
        while (rp != position):
            reps += 1
            delay = (abs(rp - position))*1.2/Speed[unit]
            if ldelay < delay:
                print("Motor going in wrong direction")
                client.write_register(0x7D, 0x20, unit=unit)
                client.write_register(0x7D, 0x0, unit=unit)
                #client.write_register(0x7D, 0x2, unit=unit)
                #client.write_register(0x0387, 0, unit=unit)
                #client.write_register(0x7D, 0x8, unit=unit)
                break
            if ldelay == delay and reps == 5:
                print("Motor not going from",rp,"to",position)
                #client.write_register(0x0E01, 0, unit=unit)
                #client.write_register(0x0387, 0, unit=unit)
                break
            msg = "Wait " + str(int(10.0*delay)/10.0) + " sec"
            #tk.Label(page[unit], font=20, foreground="#000000", text=msg).place(x=50, y=240, width=350, height=25)
            print("WAIT",delay,"sec to goto",position,"from",rp,"at",Speed[unit])
            ldelay = delay
            sleep(delay)
            read = client.read_holding_registers(0x00C7, 1, unit=unit)
            rp = read.registers[0]
            #tk.Label(page[unit], font=20, foreground="#F0F0F0", text=msg).place(x=50, y=240, width=350, height=25)
            #e1 = tk.Label(page[unit], font=12, bg="#FFFFFF", text="WAIT", justify='right')
        print("readDelay OUT",rp)
        self.position = rp
        return rp


    def readMotor(self):
        """
		Read the position of the 'unit' motor.

		:param unit: motor index number
		:return: motor position in user steps.
		"""
        global tk
        unit = self.unit
        location = self.location

        if TEST:
            #self.connectMotor()
            self.position = 1000
            return 1000

        # log.debug("READING REGISTER ")
        if self.client:
            read = self.client.read_holding_registers(0x00D7, 1, unit=unit)
            upprpos = read.registers[0]
            print("READ MOTOR", unit, "LOC", location, "POS", self.position)
            read = self.client.read_holding_registers(0x00C7, 1, unit=unit)
            log.debug(read)
            location = read.registers[0] 
            self.closeMotor(self.client)
        else:
            warn(unit, 434)
            return

        self.position = location
        self.location = location
    
        T.setLabel(unit, location)
        return location

    def sendMotor(self, location):
        """
        Send the 'unit' motor to the user location.

        :param unit: motor index number
               location: motor position 
        :return: motor location in user steps.
        """

        unit = self.unit
        client = self.client
        #location = self.location
        print("")
        print("sendMotor", unit, location)

        if (isinstance(location, str)):
            location = T.getLabel(unit)
            #print("sendMotor string", location)
        # log.debug("Write Coils "+str(joglocation))

        delta = location - self.readMotor()
        print("CLIENT",unit,self.client)
        if client and I.outOfRange(unit, delta) > 0:
            print("SEND IS OUT OF RANGE RETURN")
            return
        if client:
            setPosition = int(location) 
            print("SEND WRITE TRY ",unit," TO ",setPosition)
            client.write_register(0x7D, 0x20, unit=unit)
            #client.write_register(0x7D, 0x0, unit=unit)
            client.write_register(0x1801, 1, unit=unit)
            client.write_register(0x0383, 1, unit=unit)
            client.write_register(0x1805, int(Speed[unit]), unit=unit)
            if int(delta) > 0:
                #client.write_register(0x7D, 0x4000, unit=unit)
                #client.write_register(0x7D, 0x0, unit=unit)
                print("SEND MOTOR FWD", unit, self.position)
            if int(delta) < 0:
                #client.write_register(0x7D, 0x8000, unit=unit)
                #client.write_register(0x7D, 0x0, unit=unit)
                print("SEND MOTOR REV", unit, self.position)
            client.write_register(0x1803, setPosition, unit=unit)
            client.write_register(0x7D, 0x8, unit=unit)
            rp = self.readDelay(setPosition)
            if unit > 20:
                client.write_register(0x7D, 0x20, unit=unit)
                client.write_register(0x7D, 0x0, unit=unit)
                client.write_register(0x1801, 1, unit=unit)
                client.write_register(0x1805, int(Speed[unit]), unit=unit)
                client.write_register(0x1803, setPosition - 10, unit=unit)
                client.write_register(0x7D, 0x8, unit=unit)
                rp = self.readDelay(setPosition)
                client.write_register(0x7D, 0x20, unit=unit)
                client.write_register(0x7D, 0x0, unit=unit)
                client.write_register(0x1801, 1, unit=unit)
                client.write_register(0x1805, int(Speed[unit]), unit=unit)
                client.write_register(0x1803, setPosition, unit=unit)
                client.write_register(0x7D, 0x8, unit=unit)
                rp = self.readDelay(setPosition)
            self.closeMotor(client)
            if rp == "None" or rp == "NoneType":
                warn(unit, 494)
        else:
            rp = Location[unit]
            mflag = 1
            msg = "Motor " + str(unit) +" is not available"
            print("THERE??")
            message(unit,mflag,msg)

        if unit == 1:
            slidePos = T.getRadioButn(1, tab1, page[1])
        if unit == 2:
            cmparPos = T.getRadioButn(2, tab2, page[2])
        if unit == 3:
            grat1Pos = T.getRadioButn(3, tab3, page[3])
        if unit == 4:
            grat2Pos = T.getRadioButn(4, tab4, page[4])

        I.setEntry(unit, rp)
        T.setLabel(unit, rp)
        #Location[unit] = rp
        position = rp
        #print("WRITE",unit,position,"SPD",Speed[unit])

    # this really doesn't move the motor - it only sets its internal location
    def setMotor(self, tab):
        """
		Set the motor position using the location the selected RadioButton.

		:param unit: motor index number,
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
        self.location = location


        print("SET MOTOR",unit,location,tab,source.get(),slide.get())
        # TODO: error trapping here
        self.sendMotor(location)
        self.location = location

    def stopMotor(self):
        """
		Stop the motor

		:param unit: motor index number,
		:param tab: Tab number
		:return: None
		"""
        self.client.write_register(0x7D, 0x20, unit=self.unit)
        self.client.write_register(0x7D, 0x0, unit=self.unit)


class InputControl:
    """
    This class contains motor attributes and methods
    """

    def _init_(self):
        self.t = t
        self.x = x
        self.y = y
        self.var = var
        self.lstr = lstr
        self.res = res
        self.unit = unit

    def callback(self, var, t, x, y):
        """
        Retrieve value for Entry value.

        :param var: Entry variable
        :param t: Entry point for tab 't'
        :param x: Entry x position
        :param y: Entry y position
        :return: True/False
        """
        global Location

        val = str(var.get())

        #print("CALLBACK",t,val)
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

        if int(val) < Lower[t]:
            val = str(Lower[t])
        if int(val) > Upper[t]:
            val = str(Upper[t])
        var.set(val)

        #return True

        #if t < 3:
            #e1 = tk.Label(page[t], font=12, bg="#FFFFFF", text=var.get(), justify='right')
            #e1.place(x=x+20, y=y, width=60, height=20)
        if t > 2:
            #e1 = tk.Label(page[t], font=12, bg="#FFFFFF", text=var.get(), justify='right')
            #e1.place(x=x+10, y=y+20, width=60, height=20)
            val = Location[t] - Reference[t]
            st = I.convertS2Dcd(val, Resolution[t])
            str1 = tk.StringVar()
            str1.set(str(val))
            str1.trace("w", lambda name, index, mode, sv=str1: I.callback(str1, t, 205, 145))
            e1 = tk.Label(page[t], font=12, bg="#FFFFFF", text=st, justify='right')
            e1.place(x=x, y=y-50, width=80, height=20)
            var1 = str1.get()
            var2 = str2.get()
            if I.is_number(var1) and I.is_number(var2):
                val = (float(var1) - float(var2)) * 360.0 / float(Resolution[t])
                deg = int(val)
                min = (val - float(deg)) * 60.0
                st = str(deg)+u"\u00b0"+str(abs(min))+"'"
                e1 = tk.Label(page[t], font=20, fg="#DD0000", bg="#FF55FF", text=st, state=DISABLE, justify='right')
                e1.place(x=70, y=22, width=80, height=20)

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


    def outOfRange(self, unit, delta):
        global tk, Location

        # position = int(position)
        msg = str(int(Location[unit]) + int(delta)) + " is Out of Range"
        # msg = "Out of Range"
        #print("outOfRange check ", Location[unit], delta)
        flag = 0
        if unit < 3:
            if int(Location[unit]) + int(delta) < Lower[unit]:
                flag = 1
                Location[unit] = Lower[unit]
            if int(Location[unit]) + int(delta) > Upper[unit]:
                flag = 2
                Location[unit] = Upper[unit]
        if unit > 2:
            if int(Location[unit]) + int(delta) < Lower[unit]:
                flag = 3
                Location[unit] = Lower[unit]
            if int(Location[unit]) + int(delta) > Upper[unit]:
                flag = 4
                Location[unit] = Upper[unit]
        if flag > 0:
            tk.Label(page[unit], font=20, foreground="#000000", text=msg).place(x=50, y=240, width=350, height=25)
            #print("FLAG", flag, msg, "LOC", Location[unit], delta)
        else:
            print("BLANK A")
            tk.Label(page[unit], font=20, foreground="#F0F0F0", text=msg).place(x=50, y=240, width=350, height=25)

        return flag

    def setEntry(self, t, val):
        """
        Get Entry values.

        :param t:
        :return:
        """
        global Location, e

        val = str(int(val))
        print("SETENTRY location", t, "VAL", val)

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
    '''

    '''

    def _init_(self, filename):
        self.filename = filename

    def readDflt(self):
        '''
        Read the default tablet settings.
         .
        :return: defaults filename
        '''
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

        # #print(filename)
        main.title('GAP Motor Control: using ' + str(filename))
        main.title('DEFAULT settings: ' + str(filename))
        main.config()
        return filename


    def readConfig(self):
        '''
        Read the default config settings.
        .
        :return: 
        '''

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
        '''
        Read user tablet settings.
         .
        :return: selected filename
        '''
        filename = askopenfilename(initialdir="./", title="Select file",
                                   filetypes=(("config files", "*.cfg"), ("all files", "*.*")))

        # global pos1, pos2, pos3, pos4
        # item1, item2, item3, item4 = 0
        global tab1, tab2, tab3, tab4
        global tmp1, tmp2, tmp3, tmp4

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
        print("USER ",tab2)
        filename = path.basename(filename)
        main.title('GAP Motor Control: using ' + str(filename))
        main.title('USER settings: ' + str(filename))
        print(filename)
        #update()

    def saveUser(self):
        """
        Save settings for current user.

        :return:
        """
        #T.updateTabLocations()

        filename = asksaveasfilename(initialdir="./", title="Select file",
                                     filetypes=(("config files", "*.cfg"), ("all files", "*.*")))

        # for unit in range(0,4):
        #     if unit == 1:
        #         tmp1[1][2] = Location[1]
        #     if unit == 2:
        #         tmp2[1][2] = Location[2]
        #     if unit == 3:
        #         print(tmp3)
        #         print(tmp3[1][2])
        #         tmp3[1][2] = Location[3]
        #     if unit == 4:
        #         tmp4[1][2] = Location[4]

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
        #print("STR1",str1)
        #print("STR2",str2)
        #print("STR3",str3)
        #print("STR4",str4)
        #str5 = I.convertL2S(jog1)
        #str6 = I.convertL2S(jog2)
        #str7 = I.convertL2S(jog3)
        #str8 = I.convertL2S(jog4)

        # build file
        records = []
        records.append(ttl1)
        records.append(ttl2)
        records.append(hdr1)
        records.append(str1)
        #records.append(str5)
        records.append(hdr2)
        records.append(str2)
        #records.append(str6)
        records.append(hdr3)
        records.append(str3)
        #records.append(str7)
        records.append(hdr4)
        records.append(str4)
        #records.append(str8)

        if filename == '':
            return

        # write file
        fileHandle = open(filename, "w")
        fileHandle.writelines(records)
        fileHandle.close()

    def chkPassword(self, root, pw):
        #print("chkPassword",pw.get())
        if pw.get() == 'abc123' or pw.get() == 'OOS39023' or pw.get() == '123abc':
            try:
                root.destroy()
                F.setConfig()
            except:
                pass
        else:
            pass

    def getPassword(self):
        '''

        :return:
        '''
        #F.setConfig()

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
        str1 = I.convertL2S(o[1].get()) + "\t" + I.convertL2S(z[1].get()) + "\t" + I.convertL2S(s[1].get()) + "\n"
        str2 = I.convertL2S(o[2].get()) + "\t" + I.convertL2S(z[2].get()) + "\t" + I.convertL2S(s[2].get()) + "\n"
        str3 = I.convertL2S(o[3].get()) + "\t" + I.convertL2S(z[3].get()) + "\t" + I.convertL2S(s[3].get()) + "\n"
        str4 = I.convertL2S(o[4].get()) + "\t" + I.convertL2S(z[4].get()) + "\t" + I.convertL2S(s[4].get()) + "\n"

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

        #print("wrote",filename)

        # reset current values
        for i in range(5):
            if i == 0:
                continue
            Offset[i] = int(o[i].get())
            Zero[i] = int(z[i].get())
            Speed[i] = int(s[i].get())

        win.destroy()

    def setConfig(self):
        '''

        :return:
        '''
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
        #     tk.Label(conf, font=20, foreground="#F0F0F0", text=msg).place(x=100, y=240, width=350, height=25)
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
        l[1].insert(0, Lower[1])
        l[2].insert(0, Lower[2])
        l[3].insert(0, Lower[3])
        l[4].insert(0, Lower[4])
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
    '''

    '''
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
            #print 'unit',unit,tab1,'read motor',position
            closest = T.getClosest(unit, position, tab1)
            #print("tab1",tab1)
            tmp1[closest][2] = position
            #print("tmp1",tmp1)
        if unit == 2:
            position = M2.readMotor()
            closest = T.getClosest(unit, position, tab2)
            #print("GET tab2",tab2)
            #tmp2[closest][2] = position
            #print("GET tmp2", tmp2)
        if unit == 3:
            position = M3.readMotor()
            #print(tab3)
            closest = T.getClosest(unit, position, tab3)
            #closest = 0
            #print(tab3)
            # tab3[1] = ['3', 'user', position, 'User']
        if unit == 4:
            position = M4.readMotor()
            #print(tab4)
            closest = T.getClosest(unit, position, tab4)
            #closest = 0
            #print(tab4)
            #tmp4[1][2] = position

        #print("GET Radio --- ",unit,closest,position)
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
        #global tmp1, tmp2, tmp3, tmp4
        #print(tablist)

        list_of_numbers = [int(i[2]) for i in tablist]
        closest = min(enumerate(list_of_numbers), key=lambda ix: (abs(ix[1] - position)))[0]
        nearest = list_of_numbers[closest]
        difference = position - nearest
        #print(list_of_numbers)
        #print("Closest", unit,difference,position,nearest,closest)
        if abs(difference) > 0 and unit < 3:
            message = "Motor " + str(unit) + " at " + str(position) + " is off " + str(difference) + " steps from " + str(nearest) + ". Re-click selection."
            tk.Label(page[unit], font=20, foreground="#EE0000", text=message).place(x=50, y=240, width=450, height=25)
            _warn1 = message
        elif unit < 3:
            tk.Label(page[unit], font=20, foreground="#F0F0F0", text=_warn1).place(x=50, y=240, width=450, height=25)
            _warn = ""
        # if unit == 1:
        #     tmp1[closest][2] = position
        # if unit == 2:
        #     tmp2[closest][2] = position
        # if unit == 3:
        #     tmp3[closest][2] = position
        # if unit == 4:
        #     tmp4[closest][2] = position
        #print("TAB" + str(unit), position)
        return closest

        if abs(difference) > 0:
            message = "Notice: Motor is off " + str(difference) + " steps. Click selection."
            _warn1 = message

        return closest

    def resetTab(self):
        """
        Reset settings to the llast file opened.

        :return: None
        """
        #global pos1, pos2, pos3, pos4
        pos1 = tab1
        pos2 = tab2
        pos3 = tab3
        pos4 = tab4

    def setLabel(self, t, position, x=215, y=105):
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
        '''
        Toggle show/hide limits
        '''

        global limitSet

        if limitSet == 'Show':
            limitSet = 'Hide'
        else:
            limitSet = 'Show'
        filemenu.entryconfig(2,label=limitSet + " Limits")

    def updateTabLocations(self):
        '''

        :param unit:
        :return:
        '''

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
            #print(unit,tabN)
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
        # gary this can't work - the sendMotor command doesn't use an argument of "Enter"
        tk.Button(page[1], font=20, text="Go", command=lambda: M1.sendMotor("Enter"), padx=40).place(x=215, y=175, width=30, height=20)

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
        # Gary - the argument to sendMotor is wrong...
        tk.Button(page[2], font=20, text="Go", command=lambda: M2.sendMotor("Enter"), padx=40).place(x=215, y=175, width=30, height=20)

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
        # Gary - the argument to sendMotor is wrong...
        tk.Button(page[3], font=20, text="Go", fg="red", command=lambda: M3.sendMotor("Enter"), padx=40).place(x=225, y=160, width=30, height=20)

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
        # Gary - the argument to sendMotor is wrong...
        tk.Button(page[4], font=20, text="Go", fg="red", command=lambda: M4.sendMotor("Enter"), padx=40).place(x=225, y=160, width=30, height=20)

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


"""
Motor check.
"""
F = LocalIO()
F.readConfig()
#    def __init__(self, unit, port, speed, position, resolution, zero, lower, upper):
M1 = MotorControl(1, 1, Speed[1], 0, 1, Zero[1], 0, 8000)
M2 = MotorControl(2, 2, Speed[2], 0, 1, Zero[2], 0, 1000)
M3 = MotorControl(3, 3, Speed[3], 0, 100, Zero[3], 0, 12500)
M4 = MotorControl(4, 4, Speed[4], 0, 100, Zero[4], 0, 12500)
M1.connectMotor()
M2.connectMotor()
M3.connectMotor()
M4.connectMotor()
if not TEST and not M1.connected and not M2.connected and not M3.connected and not M4.connected:
        warn()

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
