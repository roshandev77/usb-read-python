from django.shortcuts import render
import usb.core
import usb.util
from usb.core import *
import sys
import os
import binascii
import time
import serial
import itertools


def home(request):
    return render(request, 'home.html')


def output(request):
    idV = 0x04d8
    idP = 0x003f

    # doesnt seem to write anything to log?!
    os.environ['PYUSB_DEBUG'] = 'debug'
    # os.environ['PYUSB_LOG_FILENAME'] = "pyusb.log" #never written

    print("finding idVendor = {}, idProduct= {}".format(idV, idP))
    device = usb.core.find(idVendor=idV, idProduct=idP)

    if device is None:
        print("Device not found")
        exit()

    # free up the device from the kernal
    for cfg in device:
        for intf in cfg:
            if device.is_kernel_driver_active(intf.bInterfaceNumber):
                try:
                    device.detach_kernel_driver(intf.bInterfaceNumber)
                except usb.core.USBError as e:
                    sys.exit(
                        "Could not detach kernel driver from interface({0}): {1}".format(intf.bInterfaceNumber, str(e)))

    # try default conf
    print("setting configuration")
    device.set_configuration()
    print("config set")

    print("trying to claim device")
    try:
        usb.util.claim_interface(device, 0)
        print("claimed device")
    except usb.core.USBError as e:
        print("Error occurred claiming " + str(e))
        sys.exit("Error occurred on claiming")
    print("device claimed")

    # get enpoint instance
    cfg = device.get_active_configuration()
    print("***********")
    for intf in cfg:
        print("intf= " + str(intf))
    print("*********** roshan")

    # from document:
    # The HID interface is implemented on Interface 3, in addition to standard endpoint (er)0, the device supports
    # EP4 IN (device to host) interrupt transfer type, and EP5 OUT (host to device) interrupt transfer type
    #  Note: EP$ seems to come back as 0x84 while EP5 comes back as 0x05
    intf = cfg[(0, 0)]

    # get the BULK OUT descriptor
    epo = usb.util.find_descriptor(
        intf,
        # match our first out endpoint
        custom_match= \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)

    assert epo is not None

    # get the BULK IN descriptor
    epi = usb.util.find_descriptor(
        intf,
        # match our first out endpoint
        custom_match= \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)

    assert epi is not None

    usb.util.dispose_resources(device)

    print("write the data")
    # commands are 64 bytes long, first byte is command code, 02 is 'get version', it doesn't need any of the other bytes set
    try:
        # don't think I can use [0x00]*63 because it will be all pointers to same object?, call them out to be safe
        test = [0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        mybuff = b'\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        # device.write(epo,mybuff,1)         #timeout on write
        epo.write(mybuff)  # timeout on write
        # epo.write(mybuff.encode('utf-8'))   #timeout on write
    except usb.core.USBError as e:
        print("Write USBError: " + str(e))
        sys.exit()

    print("done writing")
    print("try read?")
    try:
        # info = device.read(0x81, 64)
        # info = epo.read(epi.bEndpointAddress,epi.wMaxPacketSize)
        info = epo.read(0x83, 1)
    except usb.core.USBError as e:
        print("Read USBError: " + str(e))
        sys.exit()

    # print("read: " + str(info))
    print("read: ", info)

    # print("read: " + str(type(info)))
    data = bytes(info)
    return render(request, 'home.html', {'data': data})
