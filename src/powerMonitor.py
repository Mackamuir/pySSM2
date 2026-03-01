#!/usr/bin/env python3
#This python script is only suitable for UPS Shield X1200, X1201 and X1202

import gpiod
from gpiozero import Button
import time
from subprocess import call

powerlossMessage = 0
powerfineMessage = 0
switch = Button(21)

PLD_PIN = 6
chip = gpiod.Chip('gpiochip0') # since kernel release 6.6.45 you have to use 'gpiochip0' - before it was 'gpiochip4'
pld_line = chip.get_line(PLD_PIN)
pld_line.request(consumer="PLD", type=gpiod.LINE_REQ_DIR_IN)
try:
    while True:
        pld_state = pld_line.get_value()
        if pld_state == 1:
            powerlossMessage = 0
            if powerfineMessage == 0:
                print("---AC Power OK,Power Adapter OK---")
                powerfineMessage = 1
            time.sleep(1)
        else:
            powerfineMessage = 0
            if powerlossMessage == 0:
                print("---AC Power Loss OR Power Adapter Failure---")
                powerlossMessage = 1
            time.sleep(1)
            if not switch.is_pressed:
                print("Shutdown Bypass Switch Not Pressed,Shutting Down System now...")
                call("sudo nohup shutdown -h now", shell=True)

finally:
    pld_line.release()
