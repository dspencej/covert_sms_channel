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
user_notified_of_call = False
user_notified_of_text = False
incoming_call = False
phonecall_in_progress = False
outgoing_call = False

def power_on():
    """
    Powers on the SIM7600X module.

    Args:
        None

    Returns:
        None
    """
    global ser, POWER_KEY, SERIAL_DEVICE
    print('SIM7600X is starting.')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(POWER_KEY, GPIO.OUT)
    time.sleep(0.1)
    GPIO.output(POWER_KEY, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(POWER_KEY, GPIO.LOW)
    time.sleep(20)
    ser = serial.Serial(SERIAL_DEVICE, 115200)
    ser.flushInput()
    print('SIM7600X is ready.')

def power_down():
    """
    Powers down the SIM7600X module.

    Args:
        None

    Returns:
        None
    """
    global POWER_KEY
    print('SIM7600X is logging off.')
    GPIO.output(POWER_KEY, GPIO.HIGH)
    time.sleep(3)
    GPIO.output(POWER_KEY, GPIO.LOW)
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
    print("Disclaimer: This software is provided as-is, without warranty.")
    print("Use this software at your own risk. The author and contributors")
    print("shall not be held liable for any damages or losses arising")
    print("from the use of this software. Please review the documentation")
    print("for any specific usage guidelines or precautions.\n")
    print("Initializing the SIM7600X.")

    # Read configuration
    print("Parsing the configuration file.")
    config = parse_config()
    global POWER_KEY, MY_NUMBER, IMEI_PHONE, APN_PHONE, SERIAL_DEVICE
    POWER_KEY = int(config['power_key'])
    MY_NUMBER = config['my_number']
    IMEI_PHONE = config['imei_phone']
    APN_PHONE = config['apn_phone']
    SERIAL_DEVICE = config['serial_device']
    print("Configuration settings have been set.")

    power_on()

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
        int: 0 if the response is as expected, 1 otherwise.
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
        if back not in rec_buff.decode().strip():
            print(command + ' ERROR')
            print(command + ' back:\t' + rec_buff.decode())
            return 1
        else:
            print(rec_buff.decode())
            return 0

def send_short_message(phone_number, text_message):
    """
    Sends a short message in Text Mode.

    Args:
        phone_number (str): Phone number to send the message to.
        text_message (str): Message content.

    Returns:
        None
    """
    global ser
    print("Setting SMS mode...")
    send_at("AT+CMGF=1", "OK", 1)
    print("Sending Short Message")
    answer = send_at("AT+CMGS=\"" + phone_number + "\"", ">", 2)
    if answer == 0:
        ser.write(text_message.encode())
        ser.write(b'\x1A')
        answer = send_at('', 'OK', 20)

        if answer == 0:
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
    global rec_buff
    print('Starting GPS session...')
    send_at('AT+CGPS=1,1', 'OK', 1)
    time.sleep(2)
    done = False
    while not done:
        answer = send_at('AT+CGPSINFO', '+CGPSINFO: ', 1)
        if answer == 0:
            answer = 1
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
    print("7. Manage Phone Calls")
    print("8. Exit")
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

def handle_notifications(notification):
    """
    Handles incoming call and new text message notifications.
    
    Args:
        notification (str): The notification received from the module.
        
    Returns:
        None
    """
    # Only process notifications if there is no ongoing phonecall
    global user_notified_of_call, phonecall_in_progress, rec_buff
    global user_notified_of_text, incoming_call
    if not phonecall_in_progress:
        # only notify the user once per incoming call.
        if "RING" in notification and not user_notified_of_call:
            print("Incoming call detected.")
            play_sound("ping.wav")
            user_notified_of_call = True
            incoming_call = True
            
        elif not incoming_call and user_notified_of_call:
            # Missed the call. Reset flag
            user_notified_of_call = False
            
        if "+CMTI" in notification and not user_notified_of_text:
            print("New text message received.")
            play_sound("ping.wav")
            user_notified_of_text = True
        
        elif "+CMTI" not in notification:
            # No new text message. Reset the flag.
            user_notified_of_text = False
            
        if "RING" not in notification:
            incoming_call = False
        
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
    global rec_buff, ser
    while not stop_event.is_set():
        rec_buff += ser.read(ser.inWaiting())
        lines = rec_buff.decode().split('\r\n')
        for line in lines:
            handle_notifications(line)
        time.sleep(1)


def manage_calls():
    global phonecall_in_progress, incoming_call, outgoing_call
    # New incoming phone call.
    if incoming_call and not phonecall_in_progress:
        inp = ''
        while inp != 'y' and inp != 'n':
            print("Answer incoming call? [y/n]: ")
            inp = input()
            if inp =='y':
                print("Okay, answering the call.")
                # Setup phone
                # Set volume level to 3
                send_at("AT+CLVL=3","OK",1)
                # Switch to headphones
                send_at("AT+CSDVC=1","OK",1)
                send_at("ATA","OK",1)
                phonecall_in_progress = True
                incoming_call = False
            elif inp == 'n':
                print("Declining the phone call.")
                send_at("AT+CHUP","OK",1)
                send_at("AT+CSDVC=3","OK",1)
            
    # Ongoing phone call
    elif phonecall_in_progress:
        inp = ''
        while inp != 'y' and inp != 'n':
            print("Hang up ongoing call? [y/n]: ")
            inp = input()
            if inp == 'y':
                print("Okay, hanging up.")
                send_at("AT+CHUP","OK",1)
                send_at("AT+CSDVC=3","OK",1)
                phonecall_in_progress = False
            elif inp == 'n':
                print("Okay, returning to main menu.")
                incoming_call = False
            
    # Am I calling someone?
    elif outgoing_call:
        inp = ''
        while inp != 'y' and inp != 'n':
            print("Cancel outgoing phone call? [y/n]: ")
            inp = input()
            if inp == 'y':
                print("Okay, hanging up.")
                send_at("AT+CHUP","OK",1)
                send_at("AT+CSDVC=3","OK",1)
                outgoing_call = False
            elif inp == 'n':
                print("Okay, returning to main menu.")
            
    else:
        # Initiate new call?
        inp = ''
        while inp != 'y' and inp != 'n':
            print("Would you like to make an outgoing phone call? [y/n]: ")
            inp = input()
            if inp == 'y':
                print("Enter recipient's phone number (e.g., +123456789) or 'c' to cancel: ")
                phone_number = input()
                if phone_number == 'c':
                    print("Returning to main menu.")
                    break
                else:
                    outgoing_call = True
                    print("Calling " + str(phone_number) + ".")
                    # Setup phone
                    # Set volume level to 3
                    send_at("AT+CLVL=3","OK",1)
                    # Switch to headphones
                    send_at("AT+CSDVC=1","OK",1)
                    # Start the call
                    send_at('ATD'+phone_number+';','OK',1)
            elif inp == 'n':
                print("Okay, returning to main menu.")
                
    
            
    

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
                print("Enter recipient's phone number (e.g., +123456789) or 'c' to cancel:")
                phone_number = input()
                if phone_number == 'c':
                    print("Returning to main menu.")
                    break
                else:
                    print("Enter message content:")
                    text_message = input()
                    send_short_message(phone_number, text_message)
            elif choice == '2':
                print("Enter recipient's phone number (e.g., +123456789) or 'c' to cancel:")
                phone_number = input()
                if phone_number == 'c':
                    print("Returning to main menu.")
                    break
                else:
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
                manage_calls()
            elif choice == '8':
                stop_event.set()
                message_thread.join()
                power_down()
                break
            else:
                print("Invalid choice, please try again.\n")
    except KeyboardInterrupt:
        stop_event.set()
        message_thread.join()
        power_down()
    except Exception as e:
        print(str(e))
        stop_event.set()
        message_thread.join()
        power_down()

if __name__ == '__main__':
    main()
