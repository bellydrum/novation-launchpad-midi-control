"""
IMPORTANT:
 All event handling goes in this file.
 Pretty much all of your tweaks and changes can go here.
 https://media0.giphy.com/media/NsIwMll0rhfgpdQlzn/200.gif
"""


import time

import arrangement
import channels
import mixer
import general
import patterns
import playlist
import screen
import transport
import ui

import device
import launchMapPages
import midi
import utils

# from classes.MPD226 import MPD226

class NovationLaunchpadHandler():

    # PAD_BUFFER = 0.1

    port = None
    init_time = None
    # last_pad_press_time = None
    button_map = 0
    mode_change_unlocked = False

    pad_states = [[False for i in range(1, 9)] for j in range(1, 9)]

    """
    Initialization
    """
    def set_port_number(self):
        self.port = self.get_port_number()

    def set_init_time(self):
        self.init_time = self.get_timestamp()

    def init_lightshow(self):
        print("Check da lights.")

        # device.midiOutMsg( long midiId, long channel, long data1, long data2 )
        # Ch 1 Note On - 144
        # Ch 10 Note On - 153, 0x99
        # Ch 10 Note Off - 137, 0x89
        # Ch 10 CC - 176, 0x
        # device.midiOutMsg(153 + (10) + (1 << 8) + (127 << 16) + (0)) #with port 0

        # device.midiOutMsg(midi.MIDI_NOTEON + (44 << 8) + (49 << 16)) #with port 0

    """
    External accessors
    """

    def get_port_number(self):
        return  device.getPortNumber()

    def get_timestamp(self):
        return time.perf_counter()

    """
    Utility methods
    """

    def set_hint_message(self, message):
        if isinstance(message, str): ui.setHintMsg(message)
        else: print(f"self.setHintMessage error:\n  Param 'message' must be of type str.")

    # def check_buffer(self, button, time_pressed):
    #     return time_pressed - self.last_pad_press_time > self.PAD_BUFFER

    # def check_for_mode_change_unlock(self, slider):
    #     if all(lock.value == slider.value for lock in [self.slider_1, self.slider_2, self.slider_3, self.slider_4]):
    #         self.mode_change_unlocked = True
    #         self.set_hint_message("Button remapping mode")
    #         print("Button remapping mode UNLOCKED.")

    # def check_for_remap(self, pad, event):
    #     """ Change the button mapping if certain conditions are met. """
    #     if self.mode_change_unlocked:
    #         if self.pad_13.held and self.pad_16.held:
    #             if pad  == self.pad_1:
    #                 self.change_button_mapping(-1)
    #                 event.handled = True
    #             elif pad == self.pad_4:
    #                 self.change_button_mapping(1)
    #                 event.handled = True

    # def change_button_mapping(self, map=1):
    #     """ Update the global button mapping mode id. """
    #     if isinstance(map, str):
    #         if map in self.INPUT_MODES: map = self.INPUT_MODES.index(map)
    #     self.button_map = (self.button_map + map) % len(self.INPUT_MODES)
    #     self.set_hint_message(f"{self.INPUT_MODES[self.button_map]} mode".upper())
    #
    #     print(f"Remapped to {self.INPUT_MODES[self.button_map].upper()} mode.")

    """
    Input handlers
    """

    def handle_pad_press(self, event, pad, row, col, state):
        """ Put pad press code here.
        """
        print(f'Pressed pad in row {row} and col {col} -- {state}')

        if self.button_map == 0:
            """ Default button mapping events go here. """

        elif self.button_map == 1:
            """ UI button mapping events go here. """

        elif self.button_map == 2:
            """ Transport button mapping events go here. """

        event.handled = True

    def handle_pad_release(self, event, pad, row, col, state):
        """ Put pad release code here.
        """
        # print(f'Released pad in row {row} and col {col} -- {state}.')

        if self.button_map == 0:
            """ Default button mapping events go here. """

        elif self.button_map == 1:
            """ UI button mapping events go here. """

        elif self.button_map == 2:
            """ Transport button mapping events go here. """

        event.handled = True

    def handle_top_button_press(self, event, button):
        """ Handle top row button presses here.
        """
        print(f'Pressed top button {button}.')

        event.handled = True

    def handle_top_button_release(self, event, button):
        """ Handle top row button release here.
        """
        # print(f'Released top button {button}.')

        event.handled = True

    def handle_side_button_press(self, event, button):
        """ Handle side column button presses here.
        """
        print(f'Pressed side button {button}.')

        event.handled = True

    def handle_side_button_release(self, event, button):
        """ Handle side column button releases here.
        """
        # print(f'Released side button {button}.')

        event.handled = True

    """
    Other event handlers
    """
    def handle_beat(self, value):
        """ Respond to beat indicators. Value is 1 at bar, 2 at beat, 0 at off.
        """
        print(value)