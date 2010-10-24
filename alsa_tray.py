#!/usr/bin/python
# -*- coding: UTF-8 -*-

############################################################################
##                                                                        ##
## ALSA Tray - provides a tray icon for setting ALSA mixers volume        ##
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


"""Provides a systray icon and a command line interface for setting the
volume of the ALSA Mixers.

SYNOPSIS:
    alsa-tray [options]
    alsa-tray [options] [+|-]<Value>
    alsa-tray [options] [+|-]mute

USAGE:
    * Run in systray:
        alsa-tray, alsa-tray --tray, +tray

    * Change the volume:
        * Increase volume:
            alsa-tray +<value>
        * Decrease volume:
            alsa-tray -<value>
        * Set volume to a specific value:
            alsa-tray <value>
        where <value> is a number between 0 and 100.

    * Mute/Unmute the volume:
        * Mute:
            alsa-tray +mute
        * Unmute:
            alsa-tray -mute
        * Toggle mute/Unmute
            alsa-tray mute

    * Liste of available mixers:
        alsa-tray --mixer-list

    * Liste of available cards:
        alsa-tray --card-list

    * Help (this what you are reading):
        alsa-tray --help, -h, -?

OPTIONS:
    * Select mixer:
        --mixer=<MixerName>
        where <MixerName> is the name of the mixer.
        The default mixer is 'Master'. The list of available mixers can
        be obtained with 'alsa-tray --mixer-list'.

    * Select card:
        --card=<Card>
        where <Card> is the number of the card.
        The default card is 'hw:0'. The list of available cards can
        be obtained with 'alsa-tray --card-list'.

    * Notifications:
        +notify, --notify
            Enable notifications
        -notify
             Disable notifications

    * Debug mode:
        +debug, --debug
            Enable debug mode
        -debug
            Disable debug mode

EXAMPLES:
    * Increase the volume of 5%:
        alsa-tray +5

    * Set volume to 42% and show a notification:
        alsa-tray +notify 42

    * Mute the volume:
        alsa-tray +mute

    * Launch in systray with debugging infos and "Master" mixer selected:
        alsa-tray --debug --mixer=Master

    * Set the volume of the second sound card to 100%:
        alsa-tray --card=hw:1 100

    * Launch in systray and set the volume to 80% and muted:
        alsa-tray +tray +mute 80
"""

__version__ = "0.3"
__author__ = "Fabien Loison <flo@flogisoft.com>"
__copyright__ = "Copyright © 2010 Fabien LOISON"
__appname__ = "ALSA Tray"
__website__ = "http://software.flogisoft.com/alsa-tray/"


import sys
import os

try:
    import alsaaudio
except ImportError:
    print("E: pyAlsaAudio is not available")
    sys.exit(2)
try:
    import gobject
    import gtk
    import pygtk
    pygtk.require("2.0")
    PYGTK = True
except ImportError:
    PYGTK = False
try:
    import dbus
    from dbus.mainloop.glib import DBusGMainLoop
    DBUS = True
except ImportError:
    DBUS = False
try:
    import pynotify
    NOTIFY = True
except ImportError:
    NOTIFY = False


MIXER = "Master"
CARD = 0 #hw:0
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
DEBUG = False
CLI = False
GUI = False
CLI_OPTS = {
        'volume': "+0",
        'mute': "none",
        'notify': "none"
        }
CARD_LIST = []
MIXER_LIST = {}

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
        menu_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
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
        self.menu.append(menu_about)
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
        if DBUS:
            try:
                MMKeys(self)
            except dbus.exceptions.DBusException, detail:
                if DEBUG:
                    print("W: Multimedia key support non available:\n%s" % detail)
                else:
                    print("W: Multimedia key support non available...")
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
        menu_about.connect("activate", self.on_menu_about_activate)
        menu_quit.connect("activate", self.on_menu_quit_activate)
        #### Timer ####
        self._timer = Timer(800, self._update_infos)
        self._timer.start()

    def _update_infos(self):
        #Mixer
        mixer = alsaaudio.Mixer(control=MIXER, cardindex=CARD)
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
        mixer = alsaaudio.Mixer(control=MIXER, cardindex=CARD)
        volume = mixer.getvolume()[0]
        #Calculate the new volume
        volume = volume + value
        if volume > 100:
            volume = 100
        elif volume < 0:
            volume = 0
        #Show notification
        if notify:
            notify(volume)
        #Set the volume
        mixer.setvolume(volume)
        #Update information
        self._update_infos()

    def _toggle_mute(self, notify=False):
        #Mixer
        mixer = alsaaudio.Mixer(control=MIXER, cardindex=CARD)
        #Mute/Unmute
        if mixer.getmute()[0]:
            mixer.setmute(False)
        else:
            mixer.setmute(True)
        #Show notification
        if notify:
            if mixer.getmute()[0]:
                notify(0)
            else:
                notify(mixer.getvolume()[0])
        #Update infos
        self._update_infos()

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
        if self.window.get_visible():
            mixer = alsaaudio.Mixer(control=MIXER, cardindex=CARD)
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

    def on_menu_quit_activate(self, widget):
        gtk.main_quit()

    def on_menu_about_activate(self, widget):
        aboutdlg = gtk.AboutDialog()
        aboutdlg.set_name(__appname__)
        aboutdlg.set_version(__version__)
        aboutdlg.set_copyright(__copyright__)
        aboutdlg.set_website(__website__)
        aboutdlg.set_logo_icon_name(VOL_ICON[0])
        aboutdlg.set_icon_name(VOL_ICON[0])
        aboutdlg.connect("response", self.on_aboutdlg_response)
        aboutdlg.show()

    def on_aboutdlg_response(self, widget, response):
        if response < 0:
            widget.destroy()

    def on_mmkey_pressed(self, key):
        if key == "volume-up":
            self._set_volume(+5, True)
        elif key == "volume-down":
            self._set_volume(-5, True)
        elif key == "mute":
            self._toggle_mute(True)


def notify(value, default=True):
    if not NOTIFY and CLI_OPTS['notify'] != "no":
        if DEBUG:
            print("W: Notification not available:")
            print("the 'pyNotify' module is not available.")
        else:
            print("W: Notification not available...")
        return
    elif not NOTIFY:
        return
    if CLI_OPTS['notify'] == "no":
        return
    elif CLI_OPTS['notify'] == "none" and not default:
        return
    #Select icon
    icon_index = int((100 - value) * (len(OSD_ICON) - 1) / 100)
    #Notify
    notification = pynotify.Notification(
            "Volume",
            "",
            OSD_ICON[icon_index],
            )
    notification.set_hint_int32("value", value)
    notification.set_hint_string("x-canonical-private-synchronous", "")
    notification.show()


def ls_cards_mixers():
    """ List the availaible cards and mixers.

    List all the available cards and all the usable mixers of each cards.
    """
    global CARD_LIST
    global MIXER_LIST
    CARD_LIST = alsaaudio.cards()
    for card_name in CARD_LIST:
        MIXER_LIST[card_name] = {
                'pretty_name': "%s (hw:%i)" % (card_name, CARD_LIST.index(card_name)),
                'mixers': [],
                }
        for mixer_name in alsaaudio.mixers(CARD_LIST.index(card_name)):
            mixer = alsaaudio.Mixer(control=mixer_name, cardindex=CARD_LIST.index(card_name))
            if len(mixer.switchcap()) == 1 and mixer.switchcap()[0] in \
               ("Playback Mute", "Joined Playback Mute"):
                try:
                    mixer.getmute()
                    mixer.getvolume()
                except alsaaudio.ALSAAudioError:
                    pass
                else:
                    MIXER_LIST[card_name]['mixers'].append(mixer_name)


def select_default_card():
    """Select the default card.
    
    Select the first card that haves an usable mixer.
    """
    if len(CARD_LIST) > 0:
        global CARD
        for card_name in CARD_LIST:
            if len(MIXER_LIST[card_name]['mixers']) > 0:
                CARD = CARD_LIST.index(card_name)
                return
    else:
        print("E: No sound card found.")
        sys.exit(7)


def select_default_mixer(card):
    """Select the default mixer of the given card.

    If 'Master' available, select it, else select PCM if available, else
    select the first usable mixer.
    
    Argument:
        * card -- the card index
    """
    if check_card(card):
        global MIXER
        if len(MIXER_LIST[CARD_LIST[card]]['mixers']) == 0:
            print("E: No usable mixer for card 'hw:%i'." % card)
            sys.exit(6)
        if check_mixer("Master", card):
            MIXER = "Master"
        elif check_mixer("PCM", card):
            MIXER = "PCM"
        else:
            MIXER = MIXER_LIST[CARD_LIST[card]]['mixers'][0]


def check_card(card):
    """Check if the given card is available
    
    Argument:
        * card -- the card index

    Returns:
        True if the card is available, False else.
    """
    if card <= len(CARD_LIST)-1 and card >= 0:
        return True
    else:
        return False


def check_mixer(mixer_name, card):
    """Check if the given mixer of the given card is available
    
    Argument:
        * mixer_name -- the mixer name
        * card -- the card index

    Returns:
        True if the mixer is available, False else.
    """
    if mixer_name in MIXER_LIST[CARD_LIST[card]]['mixers']:
        return True
    else:
        return False


if __name__ == "__main__":
    #List available cards and mixers
    ls_cards_mixers()
    #Select default card and mixer
    select_default_card()
    select_default_mixer(CARD)
    #Parse args
    if len(sys.argv) > 1:
        for i in range(1, len(sys.argv)):
            if sys.argv[i] in ("+tray", "--tray"):
                GUI = True
            elif sys.argv[i] ==  "-tray":
                GUI = False
            elif sys.argv[i] in ("+debug", "--debug"):
                DEBUG = True
            elif sys.argv[i] == "-debug":
                DEBUG = False
            elif sys.argv[i] in ("+notify", "--notify"):
                CLI_OPTS['notify'] = "yes"
            elif sys.argv[i] == "-notify":
                CLI_OPTS['notify'] = "no"
            elif sys.argv[i] == "mute":
                CLI_OPTS['mute'] = "toggle"
                CLI = True
            elif sys.argv[i] == "+mute":
                CLI_OPTS['mute'] = "mute"
                CLI = True
            elif sys.argv[i] == "-mute":
                CLI_OPTS['mute'] = "unmute"
                CLI = True
            elif len(sys.argv[i]) >= 1 and len(sys.argv[i]) <= 4 and \
                 (sys.argv[i][0] in ("+", "-")) and \
                 sys.argv[i][1:].isdigit() and int(sys.argv[i][1:]) >= 0 and \
                 int(sys.argv[i][1:]) <= 100:
                CLI_OPTS['volume'] = sys.argv[i]
                CLI = True
            elif sys.argv[i].isdigit() and int(sys.argv[i]) >= 0 and \
                 int(sys.argv[i]) <= 100:
                CLI_OPTS['volume'] = sys.argv[i]
                CLI = True
            elif sys.argv[i][:8] == "--mixer=" and sys.argv[i][8:].isalnum():
                MIXER = sys.argv[i][8:]
            elif sys.argv[i] in ("--mixer-list", "--mixers-list",
                 "--list-mixer", "--list-mixers"):
                if check_card(CARD):
                    print("Available mixers:")
                    for mixer_name in MIXER_LIST[CARD_LIST[CARD]]['mixers']:
                            print("  * %s" % mixer_name)
                    sys.exit(0)
                else:
                    print("E: Unknown card 'hw:%i'." % CARD)
                    print("Run asla-tray --card-list for seeing the available cards.")
                    sys.exit(4)
            elif sys.argv[i][:7] == "--card=" and sys.argv[i][7:].isdigit():
                CARD = int(sys.argv[i][7:])
            elif sys.argv[i][:9] in ("--card=hw", "--card=HW") and \
                 sys.argv[i][9:].isdigit():
                CARD = int(sys.argv[i][9:])
            elif sys.argv[i][:10] in ("--card=hw:", "--card=HW:") and \
                 sys.argv[i][10:].isdigit():
                CARD = int(sys.argv[i][10:])
            elif sys.argv[i][:7] == "--card=" and sys.argv[i][7:].isalnum():
                if sys.argv[i][7:] in CARD_LIST:
                    CARD = CARD_LIST.index(sys.argv[i][7:])
                else:
                    print("E: Unknown card '%s'." % sys.argv[i][7:])
                    print("Run asla-tray --card-list for seeing the available cards.")
                    sys.exit(4)
            elif sys.argv[i] in ("--card-list", "--cards-list",
                 "--list-card", "--list-cards"):
                print("Available cards:")
                for card_name in CARD_LIST:
                    print("    * %s" % MIXER_LIST[card_name]['pretty_name'])
                sys.exit(0)
            elif sys.argv[i] in ("-h", "--help", "-?"):
                print("%s %s" % (__appname__, __version__))
                print(__doc__)
                print("COPYRIGHT:\n    %s\n" % __copyright__)
                print("WEB SITE:\n    %s" % __website__)
                exit(0)
            else:
                print("E: Invalide option '%s'." % sys.argv[i])
                print("Run 'alsa-tray --help' for help about CLI options.")
                sys.exit(1)

    if DEBUG:
        print("%s %s\n" % (__appname__, __version__))
        print("Python: version %s" % sys.version.replace("\n", ""))
        print("pyAlsaAudio: available")
        if PYGTK:
            print("pyGTK: available")
        else:
            print("pyGTK: unavailable")
        if DBUS:
            print("DBus Python: version %s" % dbus.__version__)
        else:
            print("DBus Python: unavailable")
        if NOTIFY:
            print("pyNotify: available")
        else:
            print("pyNotify: unavailable")
        print("")

    if not check_card(CARD):
        print("E: Unknown card 'hw:%i'." % CARD)
        print("Run asla-tray --card-list for seeing the available cards.")
        print("Search for the default card instead...")
        select_default_card()
        #Found...
        print("Card 'hw:%i' selected." % CARD)

    if not check_mixer(MIXER, CARD):
        print("E: Unknown or unusable mixer '%s' for card 'hw%i'." % (MIXER, CARD))
        print("Run asla-tray --mixer-list for seeing the available mixers.")
        print("Search for the default mixer instead...")
        select_default_mixer(CARD)
        #Found...
        print("'%s' mixer of 'hw:%i' selected."  % (MIXER, CARD))


    if CLI:
        #Mixer
        mixer = alsaaudio.Mixer(control=MIXER, cardindex=CARD)
        volume = mixer.getvolume()[0]
        mute = bool(mixer.getmute()[0])
        #Volume
        if CLI_OPTS['volume'][0] == "+":
            volume += int(CLI_OPTS['volume'][1:])
        elif  CLI_OPTS['volume'][0] == "-":
            volume -= int(CLI_OPTS['volume'][1:])
        else:
            volume = int(CLI_OPTS['volume'])
        if volume > 100:
            volume = 100
        elif volume < 0:
            volume = 0
        #Mute
        if CLI_OPTS['mute'] == "mute":
            mute = True
        elif CLI_OPTS['mute'] == "unmute":
            mute = False
        elif CLI_OPTS['mute'] == "toggle":
            mute = not mute
        #Set
        mixer.setvolume(volume)
        mixer.setmute(mute)
        #Notify
        if mute:
            notify(0, default=False)
        else:
            notify(volume, default=False)
        #Print infos
        if mute:
            print("Volume: %i%%, muted" % volume)
        else:
            print("Volume: %i%%" % volume)
    if GUI or not CLI:
        if not PYGTK:
            print("E: Can't run in systray: pyGTK is not available.")
            sys.exit(5)
        alsa_volume = ALSATray()
        try:
            gtk.main()
        except KeyboardInterrupt:
            sys.exit(0)


