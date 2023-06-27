#!/usr/bin/python
# -*- coding:utf-8 -*-

import RPi.GPIO as GPIO
import serial
import time
import threading
import configparser
import sys
import os
import pygame   

# Constants
# Do not make changes here. 
# Change the config.ini file to set these values.
POWER_KEY = None
MY_NUMBER = None
IMEI_PHONE = None
APN_PHONE = None
SERIAL_DEVICE = None

# Global variables
ser = None
rec_buff = b''
lock = threading.Lock()
stop_event = threading.Event()
notified_of_call = False

def power_on(power_key):
    """
    Powers on the SIM7600X module.

    Args:
        power_key (int): GPIO pin number for the power key.

    Returns:
        None
    """
    global ser
    print('SIM7600X is starting.')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(power_key, GPIO.OUT)
    time.sleep(0.1)
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(20)
    ser = serial.Serial(SERIAL_DEVICE, 115200)
    ser.flushInput()
    print('SIM7600X is ready.')

def power_down(power_key):
    """
    Powers down the SIM7600X module.

    Args:
        power_key (int): GPIO pin number for the power key.

    Returns:
        None
    """
    print('SIM7600X is logging off.')
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(3)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(18)
    print('Goodbye')

def init():
    """
    Initializes the SIM7600X HAT.

    Args:
        None

    Returns:
        None
    """
    print()
    print("This program is designed for a specific use case.")
    print("It assumes that you are running a Raspberry Pi (version 3 or higher)")
    print("with a SIM7600X 4G Hat installed.")
    print("If that is not correct, then this will fail.\n")
    print("Disclaimer: This software is provided as-is, without any warranties.")
    print("Use this software at your own risk. The author and contributors")
    print("shall not be held liable for any damages or losses arising")
    print("from the use of this software. Please review the documentation")
    print("for any specific usage guidelines or precautions.\n")
    print("Initializing the SIM7600X.")

    # Read configuration
    print("Parsing the configuration file.")
    config = read_config()
    global POWER_KEY, MY_NUMBER, IMEI_PHONE, APN_PHONE, SERIAL_DEVICE
    POWER_KEY = config['power_key']
    MY_NUMBER = config['my_number']
    IMEI_PHONE = config['imei_phone']
    APN_PHONE = config['apn_phone']
    SERIAL_DEVICE = config['serial_device']
    print("Configuration settings have been set.")

    power_on(int(POWER_KEY))

    # Setup Command Echo
    send_at("ATE", "OK", 1)

    print("Setting APN.")
    send_at("AT+CGDCONT=1,\"IP\",\"" + APN_PHONE + "\"", "OK", 2)
    print("Setting IMEI.")
    send_at("AT+SIMEI=" + IMEI_PHONE, "OK", 1)
    print("Turning on caller ID.")
    send_at("AT+CLIP=1","OK",1)
    print("Device is initialized.\n")

def send_at(command, back, timeout):
    """
    Sends an AT command to the module and checks the response.

    Args:
        command (str): AT command to send.
        back (str): Expected response from the module.
        timeout (int): Time to wait for the response.

    Returns:
        int: 1 if the response is as expected, 0 otherwise.
    """
    with lock:
        global rec_buff
        rec_buff = b''
        global ser
        ser.flush()
        ser.write((command+'\r\n').encode())
        time.sleep(timeout)
        if ser.inWaiting():
            time.sleep(0.01 )
            rec_buff = ser.read(ser.inWaiting())
        if back not in rec_buff.decode():
            print(command + ' ERROR')
            print(command + ' back:\t' + rec_buff.decode())
            return 0
        else:
            print(rec_buff.decode())
            return 1

def send_short_message(phone_number, text_message):
    """
    Sends a short message in Text Mode.

    Args:
        phone_number (str): Phone number to send the message to.
        text_message (str): Message content.

    Returns:
        None
    """
    print("Setting SMS mode...")
    send_at("AT+CMGF=1", "OK", 1)
    print("Sending Short Message")
    answer = send_at("AT+CMGS=\"" + phone_number + "\"", ">", 2)
    if answer == 1:
        ser.write(text_message.encode())
        ser.write(b'\x1A')
        answer = send_at('', 'OK', 20)

        if answer == 1:
            print('Message sent successfully.\n')
        else:
            print('Error')
    else:
        print('Error %d' % answer)

def send_short_message_PDU(phone_number, text_message):
    """
    Sends a short message in PDU Mode.

    Args:
        phone_number (str): Phone number to send the message to.
        text_message (str): Message content.

    Returns:
        None
    """
    print("This is not implemented, yet")

def get_gps_position():
    """
    Gets the GPS position.

    Args:
        None

    Returns:
        None
    """
    answer = 0
    print('Starting GPS session...')
    send_at('AT+CGPS=1,1', 'OK', 1)
    time.sleep(2)
    done = False
    while not done:
        answer = send_at('AT+CGPSINFO', '+CGPSINFO: ', 1)
        if answer == 1:
            answer = 0
            if ',,,,,,,,' in rec_buff.decode():
                time.sleep(1)
                continue
        else:
            print('Error %d' % answer)
            send_at('AT+CGPS=0', 'OK', 1)
            return False
        inp = input("Enter 'r' to refresh GPS location (anything else to quit): ")
        if inp == 'r':
            done = False
        else:
            done = True
        time.sleep(1.5)

def delete_all_messages():
    """
    Deletes all saved messages.

    Args:
        None

    Returns:
        None
    """
    confirmed = False
    while not confirmed:
        verify = input("Are you sure you want to delete all messages? [y/n]: ")
        if verify == 'y':
            confirmed = True
        elif verify == 'n':
            return

    print("Okay, deleting all saved messages.")
    send_at('AT+CMGF=1', 'OK', 1)
    send_at('AT+CPMS="SM","SM","SM"', 'OK', 1)
    send_at('AT+CMGD=1,4', 'OK', 2)
    print("All messages have been deleted.")

def show_all_messages():
    """
    Shows all saved messages.

    Args:
        None

    Returns:
        None
    """
    print("Loading all saved messages.")
    send_at('AT+CMGF=1', 'OK', 1)
    send_at('AT+CPMS="SM","SM","SM"', 'OK', 1)
    send_at('AT+CMGL="ALL"', 'OK', 1)

def show_unread_messages():
    """
    Shows all unread messages.

    Args:
        None

    Returns:
        None
    """
    print("Loading unread messages.")
    send_at('AT+CMGF=1', 'OK', 1)
    send_at('AT+CPMS="SM","SM","SM"', 'OK', 1)
    send_at('AT+CMGL="REC UNREAD"', 'OK', 1)

def display_menu():
    """
    Displays the main menu.

    Args:
        None

    Returns:
        None
    """
    print("============================================")
    print("1. Send Short Message (Text Mode)")
    print("2. Send Short Message (PDU Mode)")
    print("3. Get GPS Position")
    print("4. Delete All Messages")
    print("5. Display All Saved Messages")
    print("6. Display Unread Messages")
    print("7. Make Phone Call")
    print("8. Manage Incoming Call")
    print("9. Exit")
    print("============================================")
    print("Enter your choice:")

def parse_config():
    """
    Parses the configuration file.

    Args:
        None

    Returns:
        dict: Configuration parameters.
    """
    config = configparser.ConfigParser()
    config.read('config.ini')

    parameters = {}
    if 'ModuleSettings' in config:
        module_settings = config['ModuleSettings']
        if 'power_key' in module_settings:
            parameters['power_key'] = module_settings['power_key']
        if 'my_number' in module_settings:
            parameters['my_number'] = module_settings['my_number']
        if 'imei_phone' in module_settings:
            parameters['imei_phone'] = module_settings['imei_phone']
        if 'apn_phone' in module_settings:
            parameters['apn_phone'] = module_settings['apn_phone']
        if 'serial_device' in module_settings:
            parameters['serial_device'] = module_settings['serial_device']

    return parameters

def read_config():
    """
    Reads the configuration file and returns the configuration parameters.

    Args:
        None

    Returns:
        dict: Configuration parameters.
    """
    config_params = parse_config()
    if 'power_key' not in config_params:
        config_params['power_key'] = int(input("Enter the GPIO pin number for the power key: "))
    if 'my_number' not in config_params:
        config_params['my_number'] = input("Enter your phone number: ")
    if 'imei_phone' not in config_params:
        config_params['imei_phone'] = input("Enter the IMEI for the phone: ")
    if 'apn_phone' not in config_params:
        config_params['apn_phone'] = input("Enter the APN for the phone: ")
    if 'serial_device' not in config_params:
        config_params['serial_device'] = input("Enter the serial device (e.g., /dev/ttyUSB2): ")

    return config_params

def handle_notifications(notification):
    """
    Handles incoming call and new text message notifications.
    
    Args:
        notification (str): The notification received from the module.
        
    Returns:
        None
    """
    global notified_of_call
    if "RING" in notification:
        if not notified_of_call:
            print("Incoming call detected.")
            play_sound("ping.wav")
            notified_of_call = True
        else:
            pass
                
    elif "+CMTI" in notification:
        print("New text message received.")
        send_at('AT+CMGF=1', 'OK', 1)
        send_at('AT+CPMS="SM","SM","SM"', 'OK', 1)
        send_at('AT+CMGL="REC UNREAD"', 'OK', 1)
        play_sound("ping.wav")
    
    else:
        notified_of_call = False
    
    

        
def play_sound(sound_file):
    pygame.mixer.init()
    pygame.mixer.music.load(sound_file)
    pygame.mixer.music.play()

def check_for_notifications():
    """
    Checks for new notifications.
    
    Args:
        None
    
    Returns:
        None
    """
    global rec_buff
    global ser
    while not stop_event.is_set():
        rec_buff += ser.read(ser.inWaiting())
        lines = rec_buff.decode().split('\r\n')
        for line in lines:
            handle_notifications(line)
        time.sleep(1)

def initiate_phone_call(phone_number):
    """
    Initiates a phone call to phone_number

    Args:
        None

    Returns:
        None
    """
    # Setup phone
    # Set volume level to 3
    send_at("AT+CLVL=3","OK",1)
    # Switch to headphones
    send_at("AT+CSDVC=1","OK",1)
    # Start the call
    send_at('ATD'+phone_number+';','OK',1)
    print("Calling " + str(phone_number) + ". Press 'h' to hangup.")
    while True:
        inp = input()
        if (inp == 'h'):
            # End the call
            send_at("ATH","OK",1)
            # Switch to speaker
            send_at("AT+CSDVC=3","OK",1)
            break

def manage_incoming_call():
    # Setup phone
    # Set volume level to 3
    send_at("AT+CLVL=3","OK",1)
    # Switch to headphones
    send_at("AT+CSDVC=1","OK",1)
    print("Enter 'a' to answer the call or anything else to decline.")
    inp = input()
    if inp =='a':
        send_at("ATA","OK",1)
    else:
        send_at("ATH","OK",1)

def main():
    """
    Main function to run the program.

    Args:
        None

    Returns:
        None
    """
    try:
        init()     
        message_thread = threading.Thread(target=check_for_notifications)
        message_thread.start()
        print("Notification thread is running.")
        play_sound("ping.wav")
        print("If you did not hear the ping, please verify your audio configuration.\n")
        while True:
            with lock:
                display_menu()
            choice = input()
            if choice == '1':
                print("Enter recipient's phone number (e.g., +123456789):")
                phone_number = input()
                print("Enter message content:")
                text_message = input()
                send_short_message(phone_number, text_message)
            elif choice == '2':
                print("Enter recipient's phone number (e.g., +123456789):")
                phone_number = input()
                print("Enter message content:")
                text_message = input()
                send_short_message_PDU(phone_number, text_message)
            elif choice == '3':
                get_gps_position()
            elif choice == '4':
                delete_all_messages()
            elif choice == '5':
                show_all_messages()
            elif choice == '6':
                show_unread_messages()
            elif choice == '7':
                print("Enter recipient's phone number (e.g., +123456789):")
                phone_number = input()
                initiate_phone_call(phone_number)
            elif choice == '8':
                manage_incoming_call()
            elif choice == '9':
                stop_event.set()
                message_thread.join()
                power_down(int(POWER_KEY))
                break
            else:
                print("Invalid choice, please try again.\n")
    except KeyboardInterrupt:
        stop_event.set()
        message_thread.join()
        power_down(int(POWER_KEY))
    except Exception as e:
        print(str(e))
        stop_event.set()
        message_thread.join()
        power_down(int(POWER_KEY))

if __name__ == '__main__':
    main()
