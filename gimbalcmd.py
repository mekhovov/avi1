#Simple Gimbal Command Control 
#By: Brandon
#v1.0 Date:07/19/2018

#To add commands simply type the HEX found at http://www.olliw.eu/storm32bgc-wiki/Serial_Communication. 
#Example would look like 'HEX value here'+ crc or 'HEX value here' + data + crc.
#Follow the format in the command list.   

#Library Initialization
import sys
import time

import serial
import binascii
from serial import SerialException
from pynput import keyboard

'''
WIP to do list
*Set COM outside script, easy  
*combine axis conversion functions into 1, QOL 
*Reduce global variable stuff, QOL
'''

######################Global variable declaration(User Specific)#######################
baud = 115200 #Having the wrong value here will cause serial communication issues. 
com = '/dev/tty.usbserial-A50285BI' #Change this value to your COM port
crc = '3334'  #Non-mavlink CRC dummy value. Should not need to change!
sleeptime = [None, .25] #In seconds. [Movement CMD delay, Non-movement CMD delay]
  
  
#   Pitch     Roll      Yaw     
#[Min, Max, Min, Max, Min, Max] 
axislimit = [None]*6
axislimit = [-25.0, 25.0, -25.0, 25.0, -25.0, 25.0]
# axislimit = [-25.0, 25., -25.0, 25., -25.0, 25.]
axisloc = [47,48,54,55,61,62]
safelimit = [-15,15,-25,25,-100,100]

#     Pitch         Roll          Yaw     
#[speed, accel, speed, accel, speed, accel] 
speedparam = [None]*6
speedparam = [40.0, 30.0, 40.0, 30.0, 40.0, 30.0]
speedloc = [49,50,56,57,63,64]
safespeed = [30,30,30,30,50,30]

dofinterval = [None]*6
dofinterval = [16.0, 16.0, 16.0, 16.0, 16.0, 16.0]
sleepmultiplier = [None]*6
sleepmultiplier = [0.0625, 1.5, 0.0625, 1.5, 0.0625, 1.5]
zeropoint = [None]*3
zeropoint = [0, 0, 0]
axispos = [0]*3

#Global array lists 
paramlist = (axislimit, speedparam)
paramloc = (axisloc, speedloc) 
safemodelist = (safelimit, safespeed)

#Global Flags
sleep = [False]
#######################################################################################

#Initializes Serial
def serialinit():
    global ser 
    try: 
       ser = (serial.Serial(
       port = com,
       baudrate = baud,
       parity = serial.PARITY_NONE,
       stopbits = serial.STOPBITS_ONE,
       bytesize = serial.EIGHTBITS,
       timeout=1.0, 	#IMPORTANT, can be lower or higher
       inter_byte_timeout=0.1)) 
    except SerialException:  
       sys.exit('Serial port unavailable, script cancelled!') 	 
    ser.close() 
    return(ser)
	
######################################################
##################COMMAND LIST BELOW##################
######################################################
def getversionstr():
     cmd = bytes.fromhex('FA0002'+crc) 
     cmdexecute(cmd, sleep)

def getparameter(number):
     hexnum = dectohex(number)     
     cmd = bytes.fromhex('FA0203'+hexnum+crc) 
     response = cmdexecute(cmd, sleep)
     return(response)  	
	 
def homeall(): 
     setpitchrollyaw(0, 0, 0)
	 
def homepitch():
     setpitch(0)
	 
def homeroll():
     setpitch(0) 
	 
def homeyaw():
     setyaw(0)
	 
def setpitch(pitchin):
     pitch = pitchconvert(pitchin) 	 
     cmd = bytes.fromhex('FA020A'+pitch+crc)
     cmdexecute(cmd,sleep) 
	 
def setroll(rollin): 
     roll = rollconvert(rollin) 
     cmd = bytes.fromhex('FA020B'+roll+crc)
     cmdexecute(cmd,sleep) 
	 
def setyaw(yawin):
     yaw = yawconvert(yawin)
     cmd = bytes.fromhex('FA020C'+yaw+crc)
     cmdexecute(cmd,sleep) 
	 
def setpitchrollyaw(pitchin, rollin, yawin): 
     pitch = pitchconvert(pitchin)
     roll = rollconvert(rollin)
     yaw = yawconvert(yawin)
     print(pitchin, rollin, yawin)
     cmd = bytes.fromhex('FA0612'+pitch+roll+yaw+crc)
     cmdexecute(cmd,sleep, True)
######################################################
######################################################

#Checks serial response
def responsetest(ser):  
   ser.open()
   ser.write(b't')
   response = ser.readline()   
   #print(response) 
   if response == b'o':
      #print("Test response good!")
      safemode = False
   else: 
      print("""
RESPONSE ERROR: Gimbal response INOP/bad, aspects of the script will 
be put into safe mode.  This will cause overall control inaccuracies. 
 Fixes: 
   1.) Restart Gimbal.
   2.) Disconnect any extra/unnecessary serial connections.
   3.) Re-connect and check gimbal Serial/COM connections.""") 	  
      userstop = input("Would you like to continue anyways [Y/N]? ")
      if (userstop != 'y') and (userstop != 'Y'):
           sys.exit("Script cancelled.")
      else: safemode = True	  
   ser.close()
   return(safemode)
  
#Stores parameter data in pairs of two (ex:(min, max))
def paramstore(flag):	 	 
     param = [None]*2 
     for i in range(2):
        index = 0	 
        if flag == False:   
          for j in range(0,5,2): 
             param[0] = getparameter(paramloc[i][j])
             param[1] = getparameter(paramloc[i][j+1])
             for k in param:     
                paramsnip = sniphex(k,10,14) #Snips out the param value  
                paramflip = fliphex(paramsnip) #Flips hex to High-Low 
                signeddec = int(paramflip, 16) #Converts to decimal
                paramlist[i][index] = (-(signeddec & 0x8000) | (signeddec & 0x7fff))/10 #Converts signed decimal to negatives and shifts decimal point
                index += 1
        else:  
          for k in range(6): 
             paramlist[i][k] = safemodelist[i][k] 			 
     return(None)	

#Calculates the deg -> decimal interval for each axis 	 
def intervalcalc():
      index = 0
	  #wiki link: http://www.olliw.eu/storm32bgc-wiki/Inputs_and_Functions#Rc_Input_Processing 
      bound = 400 #Wiki states it should be +/-500, but 400 seems to work better (in my case)
      for i in range(0,5,2): 
         if axislimit[i] > 0:
            zeropoint[index] = axislimit[i]
         else: 
            zeropoint[index] = 0		 
         dofinterval[i] = bound/abs(axislimit[i]) #Min: interval amt to move 1 degree 
         boundadjust = bound-((bound/abs(axislimit[i+1])) * zeropoint[index]) #Accounts for zeropoint change.  
         dofinterval[i+1] = boundadjust/abs(axislimit[i+1]) #Max: interval amt to move 1 degree    
         index += 1	
      return(zeropoint)  

#Calculates sleeptime multiplier depending on speed parameters for all axises 
'''Note to self: Split speed and accel interval into separate arrays'''
def sleepmultipliercalc():
     for i in range(0,6,2):
        sleepmultiplier[i] = ((.05)/(speedparam[i]/(50))) 
        sleepmultiplier[i+1] = (.05 * speedparam[i+1])

#Data display for important info 
def datalog(safemode): 
    print('''\
*******************************
   Storm32 GIMBAL CONTROLLER
===============================	
        Min    Max              
Pitch:[{pmin}, {pmax}]        
Roll :[{rmin}, {rmax}]        
Yaw  :[{ymin}, {ymax}]
*******************************
SafeMode Active: [{sm}]   
*******************************                               
Port: {port}  Baud: [{br}]           
*******************************
DataLog:\
'''.format(pmin = axislimit[0], pmax = axislimit[1],rmin = axislimit[2], 
rmax = axislimit[3], ymin = axislimit[4], ymax = axislimit[5], 
sm = safemode, port = com, br = baud))
    return(None) 

###########################Frequently used equations/code##################################
#Decimal to 4byte HEX
def dectohex(value): 
     hexnum = hex(value)[2:]
     length =(len(hexnum))
     while length <= 3: 
        hexnum = '0'+hexnum
        length = (len(hexnum))	 		
     hexflip = fliphex(hexnum)
     return(hexflip)
	 
#Flips HEX bytes, 2 bytes at a time 
def fliphex(bytes): 
    formatbytes = "".join(reversed([bytes[i:i+2] for i in range(0, len(bytes), 2)]))
    return(formatbytes)

#snips out param DATA bytes
def sniphex(snipbytes, start, stop):
    snipbytes = (binascii.b2a_hex(snipbytes).decode("utf-8"))[start:stop]
    return(snipbytes) 
###########################################################################################
###########################################################################################	

#Checks input to see if it's in-bounds 
def pitchincheck(pitchin):
     if pitchin < axislimit[0]:
          pitchin = axislimit[0]
          print ('Pitch exceeds min travel parameter! Input was adjusted to max travel distance.') 
     elif pitchin > axislimit[1]:
          pitchin = axislimit[1]
          print ('Pitch exceeds max travel parameter! Input was adjusted to max travel distance.')
     return(pitchin) 
	 
def rollincheck(rollin): 
     if rollin < axislimit[2]:
          rollin = axislimit[2]
          print ('Roll exceeds min travel parameter! Input was adjusted to max travel distance.') 
     elif rollin > axislimit[3]:
          rollin = axislimit[3]
          print ('Roll exceeds max travel parameter! Input was adjusted to max travel distance.')  
     return(rollin) 
	 
def yawincheck(yawin):      
     if yawin < axislimit[4]:
          yawin = axislimit[4]
          print ('Yaw exceeds min travel parameter! Input was adjusted to max travel distance.') 
     elif yawin > axislimit[5]:
          yawin = axislimit[5]
          print ('Yaw exceeds max travel parameter! Input was adjusted to max travel distance.')
     return(yawin) 
#######################################################################################################
#######################################################################################################

'''Combine into 1 function'''
#Converts input to useable HEX data for gimbal (Only for certain commands!) 
def pitchconvert(pitchin):  
     pitchin = pitchincheck(pitchin) 
     sleepinput = abs(pitchin - axispos[0])  	 
     if pitchin <= zeropoint[0]:
          pitchraw = int(1500 + (dofinterval[0]*pitchin)) #Converts user roll input to movement distance
     else: 
          pitchraw = int(1500 + (dofinterval[1]*pitchin))
     pitch = dectohex(pitchraw) #Re-orders bytes to Low-High in pairs of two 
     #print(pitch) 
     sleeptime[0] = ((sleepmultiplier[0] * sleepinput)+sleepmultiplier[1])
     axispos[0] = pitchin
     sleep[0] = True
     # print('Pitch axis:', pitchin, end='\n')
     return(pitch)
	 
def rollconvert(rollin):
     rollin = rollincheck(rollin)
     sleepinput = abs(rollin - axispos[1])	 
     if rollin <= zeropoint[1]:
          rollraw = int(1500 + (dofinterval[2]*rollin)) #Converts user roll input to movement distance
     else: 
          rollraw = int(1500 + (dofinterval[3]*rollin))
     roll = dectohex(rollraw) #Re-orders bytes to Low-High in pairs of two 
     #print(roll) 
     sleeptime[0] = abs((sleepmultiplier[2] * sleepinput)+sleepmultiplier[3])
     axispos[1] = rollin
     sleep[0] = True
     # print('Roll axis:', rollin, end='\n')
     return(roll) 
	 
def yawconvert(yawin):
     yawin = yawincheck(yawin) 
     sleepinput = abs(yawin - axispos[2])	 
     if yawin <= zeropoint[2]:
          yawraw = int(1500 + (dofinterval[4]*yawin)) #Converts user roll input to movement distance
     else: 
          yawraw = int(1500 + (dofinterval[5]*yawin))
     yaw = dectohex(yawraw) #Re-orders bytes to Low-High in pairs of two 
     #print(yaw) 
     sleeptime[0] = abs((sleepmultiplier[4] * sleepinput)+sleepmultiplier[5])
     axispos[2] = yawin
     sleep[0] = True
     # print('Yaw axis:', yawin, end='\n')
     return(yaw)
###########################################################################################################################
###########################################################################################################################
	 
#Executes commands	 
def cmdexecute(cmd,sleep,pry=False):
    if not pry:
        ser.open()
    if sleep[0] == False: 	 
         ser.write(cmd)
         response = (ser.readline())		 
         time.sleep(sleeptime[1])
         #print(response)  		 
    else:
         ser.write(cmd)
         response = None
         # response = (ser.readline())
         # print(response)
         # print ('Gimbal moveing wait', end="...")
         # sys.stdout.flush()
         # time.sleep(sleeptime[0])
         # print ('Done', end="\n==========================\n")
    sleep[0] = False
    if not pry:
        ser.close()
    return(response)

class GimbalControl:
    x, y, z = 0, 0, 0
    last_dx, last_dy, last_dz = 0, 0, 0
    acc = 0
    last_time = time.time()
    last_char = None

    def __init__(self):
        self.main()

    #Intializes script
    def main(self):
        print('Initializing...')
        sys.stdout.flush()
        ser = serialinit()
        # safemode = responsetest(ser)
        # paramstore(safemode)
        # sleepmultipliercalc()
        # intervalcalc()

        ser.open()
        # self.loop()
        # setpitchrollyaw(25,25,25)
        # # setpitchrollyaw(-25,-25,-25)
        # # setpitchrollyaw(0,0,0)
        # while True:
        #  in_ = input("...")
        #  if in_ == 'stop':
        #      break
        #  pyr = list(map(int, in_.split()))
        #  setpitchrollyaw(*pyr)
        print("Done")
        # datalog(safemode)

    def reset(self):
        setpitchrollyaw(0, 0, 0)

    def move(self, dx, dy, dz, speed=1, acc=1):
        self.x += dx * (speed + 2 * acc * int(dx == self.last_dx))
        self.y += dy * (speed + 2 * acc * int(dy == self.last_dy))
        self.z += dz * (speed + 2 * acc * int(dz == self.last_dz))

        self.x = max(min(self.x, 25), -25)
        self.y = max(min(self.y, 25), -25)
        self.z = max(min(self.z, 25), -25)

        self.last_dx = dx
        self.last_dy = dy
        self.last_dz = dz

        setpitchrollyaw(self.x, self.y, self.z)

    def handle_manual(self, char):
        try:
            if char == self.last_char and time.time() - self.last_time < 1:
                self.acc += 0
            else:
                self.acc = 0
            dv = 3 + self.acc
            match char:
                case 'q':
                    self.z += dv
                case 'e':
                    self.z -= dv
                case 's':
                    self.x += dv
                case 'w':
                    self.x -= dv
                case 'a':
                    self.y -= dv
                case 'd':
                    self.y += dv
                case 'h':
                    self.x, self.y, self.z = 0, 0, 0
                case _:
                    return

            self.x = max(min(self.x, 25), -25)
            self.y = max(min(self.y, 25), -25)
            self.z = max(min(self.z, 25), -25)

            print('xyz', self.x, self.y, self.z)

            self.last_char = char
            self.last_time = time.time()

            setpitchrollyaw(self.x, self.y, self.z)
        except Exception as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    setpitchrollyaw(25, 25, 25)
    setpitchrollyaw(-25,-25,-25)
    setpitchrollyaw(0,0,0)