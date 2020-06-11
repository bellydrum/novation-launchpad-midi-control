# name=Novation Launchpad MK2

"""
HEY! YOU!
 I've made it so you don't have to change anything in this file.
 For all event handling, check next door in NovationLaunchpadHandler.py
"""

import device
import midi

from NovationLaunchpadHandler import NovationLaunchpadHandler

class DeviceInstance(NovationLaunchpadHandler):

    def OnInit(self):
        self.set_port_number()
        self.set_init_time()
        self.init_lightshow()
        print(f"Initialized Novation Launchpad on port {self.port}.")

    def OnMidiMsg(self, event):
        self.delegate_event(event)
        event.handled = False

    def OnDeInit(self):
        pass

    def OnMidiIn(self, event):
        pass

    def OnMidiOutMsg(self, event):
        pass

    def OnIdle(self):
        pass

    def OnRefresh(self, flags):
        pass

    def OnUpdateBeatIndicator(self, value):
        self.handle_beat(value)

    def delegate_event(self, event):
        if event.status == midi.MIDI_NOTEON:
            row = int(str(event.data1)[0])
            col = int(str(event.data1)[1])

            if col < 9:  # 64 pads
                if event.data2 == 127:
                    self.pad_states[row - 1][col - 1] = not self.pad_states[row - 1][col - 1]
                    self.handle_pad_press(event, event.data1, row, col, self.pad_states[row - 1][col - 1])
                elif event.data2 == 0: self.handle_pad_release(event, event.data1, row, col, self.pad_states[row - 1][col - 1])
            else:  # 8 side buttons
                if event.data2 == 127: self.handle_side_button_press(event, row)
                elif event.data2 == 0: self.handle_side_button_release(event, row)

        elif event.status == midi.MIDI_CONTROLCHANGE:
            # 8 top buttons
            if event.data2 == 127: self.handle_top_button_press(event, event.data1 - 103)
            elif event.data2 == 0: self.handle_top_button_release(event, event.data1 - 103)

mpd_device = DeviceInstance()

def OnInit():
    mpd_device.OnInit()

def OnDeInit():
    pass

def OnMidiIn(event):
    pass

def OnMidiOutMsg(event):
    pass

def OnMidiMsg(event):
    mpd_device.OnMidiMsg(event)

def OnIdle():
    pass

def OnRefresh(flags):
    pass

def OnUpdateBeatIndicator(value):
    mpd_device.OnUpdateBeatIndicator(value)
