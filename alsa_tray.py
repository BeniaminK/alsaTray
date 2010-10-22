#!/usr/bin/python
# -*- coding: UTF-8 -*-

############################################################################
##                                                                        ##
## ALSA Tray - provides a tray icon for setting ALSA volume               ##
##                                                                        ##
## Copyright (C) 2010  Fabien Loison (flo@flogisoft.com)                  ##
##                                                                        ##
## This program is free software: you can redistribute it and/or modify   ##
## it under the terms of the GNU General Public License as published by   ##
## the Free Software Foundation, either version 3 of the License, or      ##
## (at your option) any later version.                                    ##
##                                                                        ##
## This program is distributed in the hope that it will be useful,        ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of         ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          ##
## GNU General Public License for more details.                           ##
##                                                                        ##
## You should have received a copy of the GNU General Public License      ##
## along with this program.  If not, see <http://www.gnu.org/licenses/>.  ##
##                                                                        ##
############################################################################
##                                                                        ##
## WEB SITE : http://software.flogisoft.com/alsa-volume/                  ##
##                                                                       ##
#########################################################################


"""provides a tray icon for setting the volume of the ALSA Master mixer"""

__version__ = "0.1"
__author__ = "Fabien Loison <flo@flogisoft.com>"
__copyright__ = "Copyright © 2009 - 2010 Fabien LOISON"
__appname__ = "alsa-tray"


import sys
import os

import alsaaudio
import gobject
import gtk
import pygtk
pygtk.require('2.0')
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import pynotify


MIXER = "Master"

VOL_ICON = [
        "audio-volume-high-panel",   # > 66%
        "audio-volume-medium-panel", # > 33%
        "audio-volume-low-panel",    # > 0%
        "audio-volume-muted-panel",  # = 0%
        ]

OSD_ICON = [
        "notification-audio-volume-high",   # > 66%
        "notification-audio-volume-medium", # > 33%
        "notification-audio-volume-low",    # > 0%
        "notification-audio-volume-muted",  # = 0%
        ]


class Timer(object):

    """A basic timer.

    A basic timer based on gobject.timeout_add.
   
    Methods:
        * start -- start the timer
        * stop -- stop the timer
    """

    def __init__(self, interval, callback, args=[], kwargs={}):
        """ The constructor.

        Arguments:
            * interval -- the timer interval (in milliseconds)
            * callback -- the callback function
        Keyword arguments:
            * args -- arguments for the callback function
            * kwargs -- keyword arguments for the callback function
        """
        self._interval = interval
        self._callback = callback
        self._args = args
        self._kwargs = kwargs
        self._timer = None
        self._enabled = False

    def start(self):
        """ Starts the timer """
        self._enabled = True
        self._timer_loop()

    def stop(self):
        """ Stops the timer """
        self._enabled = False

    def _timer_loop(self):
        """ Main loop """
        if self._enabled:
            self._timer = gobject.timeout_add(self._interval, self._timer_loop)
            self._callback(*self._args, **self._kwargs)


class MMKeys(object):

    """Handle multimedia keys via dbus/Hal

    This class comes originally from the Volti project
    <http://code.google.com/p/volti/>
    """

    def __init__(self, main_instance):
        """Constructor"""
        loop = DBusGMainLoop()
        self.main = main_instance
        bus = dbus.SystemBus(mainloop=loop)
        for udi in self.get_inputs():
            obj = bus.get_object("org.freedesktop.Hal", udi)
            iface = dbus.Interface(obj, "org.freedesktop.Hal.Device")
            iface.connect_to_signal(
                    "Condition",
                    self.button_handler,
                    path_keyword="path",
                    )

    def hal_manager(self):
        """Hal manager"""
        bus = dbus.SystemBus()
        obj = bus.get_object(
                "org.freedesktop.Hal",
                "/org/freedesktop/Hal/Manager",
                )
        return dbus.Interface(obj, "org.freedesktop.Hal.Manager")

    def get_inputs(self):
        """Get keys"""
        return self.hal_manager().FindDeviceByCapability("input.keys")

    def button_handler(self, sender, destination, path):
        """Handle button events and pass them to main app"""
        if sender == "ButtonPressed":
            self.main.on_mmkey_pressed(destination)


class ALSATray(object):

    """The Alsa Volume tray icon"""

    def __init__(self):
        self.handle_menu_mute = True
        #### Widgets ####
        #Tray icon
        self.tray_icon = gtk.StatusIcon()
        #Slider
        self.slider = gtk.VScale()
        self.slider.set_inverted(True)
        self.slider.set_range(0, 100)
        self.slider.set_increments(1, 10)
        self.slider.set_digits(0)
        self.slider.set_size_request(-1, 150)
        self.slider.set_value_pos(gtk.POS_BOTTOM)
        #Window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_border_width(3)
        self.window.add(self.slider)
        #Menu
        self.menu_mute = gtk.CheckMenuItem("Mute")
        #
        separator0 = gtk.MenuItem()
        #
        menu_mixer0 = gtk.ImageMenuItem("GNOME ALSA Mixer")
        menu_mixer0_img = gtk.Image()
        menu_mixer0_img.set_from_icon_name(
                "gtk-preferences",
                gtk.ICON_SIZE_MENU,
                )
        menu_mixer0.set_image(menu_mixer0_img)
        #
        menu_mixer1 = gtk.ImageMenuItem("ALSA Mixer")
        menu_mixer1_img = gtk.Image()
        menu_mixer1_img.set_from_icon_name(
                "gtk-preferences",
                gtk.ICON_SIZE_MENU,
                )
        menu_mixer1.set_image(menu_mixer1_img)
        #
        menu_mixer2 = gtk.ImageMenuItem("XFCE4 Mixer")
        menu_mixer2_img = gtk.Image()
        menu_mixer2_img.set_from_icon_name(
                "gtk-preferences",
                gtk.ICON_SIZE_MENU,
                )
        menu_mixer2.set_image(menu_mixer2_img)
        #
        menu_separator1 = gtk.MenuItem()
        #
        menu_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        #
        self.menu = gtk.Menu()
        self.menu.append(self.menu_mute)
        self.menu.append(separator0)
        show_separator1 = False
        if os.path.isfile("/usr/bin/gnome-alsamixer"):
            self.menu.append(menu_mixer0)
            show_separator1 = True
        if os.path.isfile("/usr/bin/alsamixer") and \
           os.path.isfile("/usr/bin/gnome-terminal"):
            self.menu.append(menu_mixer1)
            show_separator1 = True
        if os.path.isfile("/usr/bin/xfce4-mixer"):
            self.menu.append(menu_mixer2)
            show_separator1 = True
        if show_separator1:
            self.menu.append(menu_separator1)
        self.menu.append(menu_quit)
        #### Signals ####
        #Tray icon
        self.tray_icon.connect("activate", self.on_tray_icon_activate)
        self.tray_icon.connect(
                "button-release-event",
                self.on_tray_icon_button_release_event,
                )
        self.tray_icon.connect("scroll-event", self.on_tray_icon_scroll_event)
        self.tray_icon.connect("popup-menu", self.on_tray_icon_popup_menu)
        #Slider
        self.slider.connect("value-changed", self.on_slider_value_changed)
        #Window
        self.window.connect("focus-out-event", self.on_window_focus_out_event)
        #### MM Keys ####
        mmkeys = MMKeys(self)
        #Menu
        self.menu_mute.connect("activate", self.on_menu_mute_activate)
        menu_mixer0.connect(
                "activate",
                self.on_menu_mixer_activate,
                "gnome-alsamixer &",
                )
        menu_mixer1.connect(
                "activate",
                self.on_menu_mixer_activate,
                "gnome-terminal -x alsamixer &",
                )
        menu_mixer2.connect(
                "activate",
                self.on_menu_mixer_activate,
                "xfce4-mixer &",
                )
        menu_quit.connect("activate", self.quit)
        #### Timer ####
        self._timer = Timer(1000, self._update_infos)
        self._timer.start()

    def _update_infos(self):
        #Mixer
        mixer = alsaaudio.Mixer(control=MIXER)
        volume = mixer.getvolume()[0]
        mute = mixer.getmute()[0]
        #Tray icon
        if mute:
            icon_index = len(VOL_ICON) - 1
            self.tray_icon.set_tooltip("Volume: mute")
            self.handle_menu_mute = False
            self.menu_mute.set_active(True)
            self.handle_menu_mute = True
        else:
            icon_index = int((100 - volume) * (len(VOL_ICON) - 1) / 100)
            self.tray_icon.set_tooltip("Volume: %i%%" % volume)
            self.handle_menu_mute = False
            self.menu_mute.set_active(False)
            self.handle_menu_mute = True
        self.tray_icon.set_from_icon_name(VOL_ICON[icon_index])
        #Slider
        self.slider.set_value(volume)

    def _set_win_position(self):
        screen, geometry, orient = self.tray_icon.get_geometry()
        #Calculate window position
        if orient == gtk.ORIENTATION_HORIZONTAL:
            if geometry.y < screen.get_height()/2: #Panel at TOP
                win_x = geometry.x
                win_y = geometry.y + geometry.width
            else:                                  #Panel at BOTTOM
                win_x = geometry.x
                win_y = geometry.y - geometry.width - 150
        else:
            if geometry.x < screen.get_width():    #Panel at LEFT
                win_x = geometry.x + geometry.width
                win_y = geometry.y
            else:                                  #Panel at RIGHT
                win_x = geometry.x - geometry.width - 32
                win_y = geometry.y
        #Move window
        self.window.move(win_x, win_y)

    def _set_volume(self, value, notify=False):
        #Mixer
        mixer = alsaaudio.Mixer(control=MIXER)
        volume = mixer.getvolume()[0]
        #Calculate the new volume
        volume = volume + value
        if volume > 100:
            volume = 100
        elif volume < 0:
            volume = 0
        #Show notification
        if notify:
            self._notify(volume)
        #Set the volume
        mixer.setvolume(volume)
        #Update information
        self._update_infos()

    def _toggle_mute(self, notify=False):
        #Mixer
        mixer = alsaaudio.Mixer(control=MIXER)
        #Mute/Unmute
        if mixer.getmute()[0]:
            mixer.setmute(False)
        else:
            mixer.setmute(True)
        #Show notification
        if notify:
            if mixer.getmute()[0]:
                self._notify(0)
            else:
                self._notify(mixer.getvolume()[0])
        #Update infos
        self._update_infos()

    def _notify(self, value):
        #Select icon
        icon_index = int((100 - value) * (len(OSD_ICON) - 1) / 100)
        #Notify
        notification = pynotify.Notification(
                "Volume",
                "",
                OSD_ICON[icon_index],
                )
        notification.set_hint_int32("value", value);
        notification.set_hint_string("x-canonical-private-synchronous", "")
        notification.show()

    def on_tray_icon_activate(self, widget):
        if self.window.get_visible():
            self.window.hide()
        else:
            self._set_win_position()
            self.window.show_all()

    def on_tray_icon_button_release_event(self, widget, event):
        if event.button == 2: #Middle click
            self._toggle_mute(False)

    def on_tray_icon_scroll_event(self, widget, event):
        if event.direction == gtk.gdk.SCROLL_UP:
            self._set_volume(+5, False)
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self._set_volume(-5, False)

    def on_tray_icon_popup_menu(self, widget, button, time):
        self.menu.show_all()
        self.menu.popup(None, None, None, button, time)

    def on_slider_value_changed(self, widget):
        mixer = alsaaudio.Mixer(control=MIXER)
        mixer.setmute(False)
        mixer.setvolume(int(self.slider.get_value()))
        self._update_infos()

    def on_window_focus_out_event(self, widget, event):
        self.window.hide()

    def on_menu_mute_activate(self, widget):
        if self.handle_menu_mute:
            self._toggle_mute(False)

    def on_menu_mixer_activate(self, widget, command):
        os.popen(command)

    def quit(self, widget, data=None):
        gtk.main_quit()

    def on_mmkey_pressed(self, key):
        if key == "volume-up":
            self._set_volume(+5, True)
        elif key == "volume-down":
            self._set_volume(-5, True)
        elif key == "mute":
            self._toggle_mute(True)


if __name__ == "__main__":
    #Show infos
    print("ALSA Tray - %s\n" % __doc__)
    print("Version: %s" % __version__)
    print(__copyright__)
    #Run
    alsa_volume = ALSATray()
    try:
        gtk.main()
    except KeyboardInterrupt:
        sys.exit(0)


