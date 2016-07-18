from __future__ import print_function
print('Start')
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'remote'))
import time
import sem
import struct
from sem_v3_lib import *


print("So far so good.")



SampleName = 'time trial'
ImageWidth = 512
ImageHeight = 512
NumImages = 1
bpp = 16
ScanSpeed = 6
CaptureSE = True
CaptureBSE = False
SEFileName = '%s, %dx%dx%d, %d bpp, little endian, SE.raw' % (SampleName, ImageWidth, ImageHeight, NumImages, bpp)
BSEFileName = '%s, %dx%dx%d, %d bpp, little endian, BSE.raw' % (SampleName, ImageWidth, ImageHeight, NumImages, bpp)


# read SharkSEM message from data connection (callbacks)
def ReadMessage(conn):
    #receive the message header
    msg_name = conn._RecvStrD(16)
    hdr = conn._RecvStrD(16)
    v = struct.unpack("<IIHHI", hdr)
    body_size = v[0]

    #get fn name
    cb_name = DecodeString(msg_name)

    #receive the body
    cb_body = conn._RecvStrD(body_size)

    #finished reading message
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

def main():
    global SEFileName
    global BSEFileName



    if conn<0:
        print("Error: Unable to connect to SEM")
        return

        

    ViewField = m.GetViewField()*1000 # View field in microns.
    Voltage = m.HVGetVoltage()/1000; # Voltage in keV.

    SEFileName = '%s, %d keV, %dx%dx%d, %g um wide, %d bpp, little endian, SE.raw' % (SampleName, Voltage, ImageWidth, ImageHeight, NumImages, ViewField, bpp)
    BSEFileName = '%s, %d keV, %dx%dx%d, %g um wide, %d bpp, little endian, BSE.raw' % (SampleName, Voltage, ImageWidth, ImageHeight, NumImages, ViewField, bpp)


    # Assign SE to channel 0 and BSE to channel 1.
    m.DtSelect(0, 0)
    m.DtSelect(1, 1)

    # Enable each, 8 or 16 bits/pixel.
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
    
    m.AutoWD(0)
    time.sleep(30)

    

    # Loop through a bunch of images..
    #for i in range(NumImages):
        #Take an image.
    res = m.ScScanXY(1, ImageWidth, ImageHeight, 0, 0, ImageWidth-1, ImageHeight-1, 1)        
    print("Scanning image #1")
    time.sleep(1)

    #Let the image come in as it is acquired and then write it.
    WriteImage(m)

    print("\n\n")
    time.sleep(1)  
    print('Done')

#Connect to the SEM SharkSEM interface.
m = sem.Sem()
conn = m.Connect('localhost', 8300) 

main()



