# name=Novation Launchpad MK2

"""
HEY! YOU!
 I've made it so you don't have to change anything in this file.
 For all event handling, check next door in NovationLaunchpadHandler.py
"""

from NovationLaunchpadHandler import NovationLaunchpadHandler

class DeviceInstance(NovationLaunchpadHandler):

    def OnInit(self):
        self.set_port_number()
        self.set_init_time()
        self.init_lightshow()
        print(f"Initialized Novation Launchpad on port {self.port}.")

    def OnMidiMsg(self, event):
        event.handled = False
        self.delegate_event(event)

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
        status = event.status
        try:
            if self.events[status] == "Note On":
                self.delegate_note_on(event)
            elif self.events[status] == "Control Change":
                self.delegate_control_change(event)
            else:
                print(f"Event status {status} not found in self.events.")
                event.handled = True
        except KeyError:
            print(f"self.delegate_event error:\n  Event status {status} does not exist.")

    def delegate_note_on(self, event):
        # pad = self.get_pad(event.controlNum)
        # if pad:
        #     time_pressed = self.get_timestamp()
        #     if self.check_buffer(pad, time_pressed):
        #         self.last_pad_press_time = time_pressed
        #         pad.on = not pad.on
        #         pad.held = True
        #         self.check_for_remap(pad, event)
        #         self.handle_pad_press(event, pad)
        event.handled = True

    def delegate_note_off(self, event):
        # pad = self.get_pad(event.controlNum)
        # if pad:
        #     pad.held = False
        #     self.handle_pad_release(event, pad)
        event.handled = True

    def delegate_control_change(self, event):
        pass

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
