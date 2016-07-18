# -*- coding: utf-8 -*-
from __future__ import print_function
print('Start')
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'remote'))
import time
import sem
import struct
#import base64
from sem_v3_lib import *
#from io import BytesIO
#import msvcrt
#import numpy as np

#-------------------------------------------------------------------------------------------------------------------------------------------------------------

print("So far so good.")

SampleName = 'none'

ImageWidth = 512

ImageHeight = 512

NumImages = 1

bpp = 16

ScanSpeed = 2

CaptureSE = True

CaptureBSE = False


#Connect to the SEM SharkSEM interface.
m = sem.Sem()
conn = m.Connect('localhost', 8300)


def ReadMessage(conn):
    # receive the message header
    msg_name = conn._RecvStrD(16)
    hdr = conn._RecvStrD(16)
    v = struct.unpack("<IIHHI", hdr)
    body_size = v[0]

    # get fn name
    cb_name = DecodeString(msg_name)
                   
    # receive the body
    cb_body = conn._RecvStrD(body_size)

    # finished reading message
    return (cb_name, cb_body)


def WriteImage(m):

    NumChannels = 0

    if CaptureSE == True:
        SEfile = open(SEFileName, "ab")
        NumChannels += 1

    if CaptureBSE == True:
        BSEfile = open(BSEFileName, "ab")
        NumChannels += 1


    bytes_read = 0
    bytesperpixel = bpp/8
    

    while bytes_read < ImageWidth*ImageHeight*bytesperpixel*NumChannels:
        (cb_name, cb_body) = ReadMessage(m.connection)
        v = struct.unpack("<IiIiI", cb_body[0:20])

        # Channel 0, write SE image.
        if v[1] == 0 and CaptureSE == True:
            SEfile.write(cb_body[20:])
            bytes_read = bytes_read + v[4]

        # Channel 1, write BSE image.
        if v[1] == 1 and CaptureBSE == True:
            BSEfile.write(cb_body[20:])
            bytes_read = bytes_read + v[4]

        # When we are done, close the files.
        if bytes_read >= ImageWidth*ImageHeight*bytesperpixel*NumChannels:        
            if CaptureSE == True:
                 SEfile.close()

            if CaptureBSE == True:
                 BSEfile.close()

        time.sleep(1)

def main(x, y):
    global SEFileName
    global BSEFileName
    
    if conn<0:
        print("Error: Unable to connect to SEM")
        return


    ViewField = m.GetViewField()*1000 # View field in microns.
    Voltage = m.HVGetVoltage()/1000; # Voltage in keV.


    SEFileName = '(' + str(x) + ', ' + str(y) + ') ' + '%s, %d keV, %dx%dx%d, %g um wide, %d bpp, little endian,SE.raw' % (SampleName, Voltage, ImageWidth, ImageHeight, NumImages, ViewField, bpp)
    #BSEFileName = '%s, %d keV, %dx%dx%d, %g um wide, %d bpp, little endian, BSE.raw' % (SampleName, Voltage, ImageWidth, ImageHeight, NumImages, ViewField, bpp)


    #Assign SE to channel 0 and BSE to channel 1.
    m.DtSelect(0, 0)
    m.DtSelect(1, 1)


    #Enable each, 8 or 16 bits/pixel.
    if CaptureSE == True:
        m.DtEnable(0, 1, bpp)
    else:
        m.DtEnable(0, 0)
    if CaptureBSE == True:
        m.DtEnable(1, 1, bpp)
    else:
        m.DtEnable(1, 0)


    # make sure scanning is inactive
    m.ScStopScan()
    m.ScSetSpeed(ScanSpeed)

    
    #move SEM to that location
    m.StgMoveTo(x, y)
        
    time.sleep(5)
        
    #Autofocus on that point        
    m.AutoWD(0)
    
    
    time.sleep(40)


    for i in range(NumImages):
        # Take an image.
        print("Scanning image# " + str(i))
        time.sleep(1)

        res = m.ScScanXY(1, ImageWidth, ImageHeight, 0, 0, ImageWidth-1, ImageHeight-1, 1)
        
        # Let the image come in as it is acquired and then write it.
        WriteImage(m)

        print("\n\n")
        
    print("\n\n")

    time.sleep(1)

#    if CaptureSE == True:
#        print("\n" + str(i+1) + " images written to " + SEFileName)
#
#    if CaptureBSE == True:
#        print("\n" + str(i+1) + " images written to " + BSEFileName)

    print('Done')
    
    return

#-------------------------------------------------------------------------------------------------------------------------------------------------------------

#args will hold the arguments for the functions. This is the format of the arguments:
#args = [x_0, y_0, x_max, x_min, y_max, y_min, delta]
#Edit the list below to use its arguments.
args = [0, 35]

def calc_coords(x_0, y_0, x_max = 102, x_min = -2, y_max = 37, y_min = -65, delta = 1.8):
    """This function simply creates a rectangular area to scan over. """ \
    """The min and max values are ideally where the stage touches the chamber walls. """\
    """x_0 and y_0 must lie within this area. This function will move the electron """\
    """beam to the given point, then move onto the next one based on the spacing delta."""
    
    if x_0 > x_max:
        return 'Error: input x must be smaller'
        
    elif x_0 < x_min:
        return 'Error: input x must be larger'
        
    elif y_0 > y_max:
        return 'Error: input y must be smaller'
        
    elif y_0 < y_min:
        return 'Error: input y must be larger'
    
    
    
#The following makes a list of 2-element tuples
#and they will be used as the coordinates of the beam's location
    
   #dummy variable, may be removed if we make the sub while-->for    
    x_n = x_min + 1
    
   #empty list where we'll store the coordinates 
    coords = []
    
   #define indices         
    n = 0
    m = 0
    
   #"dummy variable" used to get the while loop started 
    while x_n >= x_min:                         
                    
        x_n = x_0 - n*delta                 #new x posistion
        y_m = y_0 + m*delta                 #new y position
        n = n+1
                                    
        if x_n < x_min:                     #once we reach x_min, set x = x_min
            x_n = x_min               
            n = 0                           #reset n index when we reach the end
            m = m + 1                       #increase m index by 1 to change y_m
                    
        if y_m > y_max:                     #place a bound on the y value
            y_m = y_max           
                
       #add the calculated x_n, y_m to the list coord         
        coords = coords + [(round(x_n, 1), round(y_m, 1)),]
        
       #break the loop when we reach the bottom corner                 
        if y_m == y_max and x_n == x_min:
            break
    
    return coords
    
    

def TakeImgs(*args):
    """This function takes the coordinates calculated from calc_coords and feeds """\
    """them to the SEM. At each point, an image is taken. """\
    """CAUTION: please make sure to alter the max and min values if a custom stage is being used."""

    coords = calc_coords(*args)

    #Now that we have the list, we can use it to assign the coordinates to the SEM
    ##########
    ##########
    
    
    #define a certain magical index
    j = 0
    while j < len(coords):
        x, y = coords[j]
        
        ##move SEM to that location
        #m.StgMoveTo(x, y)
        #
        ##Autofocus on that point        
        #m.AutoWD(0)
        
        #call main function at coordinates
        main(x, y)
        
        j = j+1