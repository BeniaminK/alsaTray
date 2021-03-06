============================================================================
                                   ALSA TRAY
============================================================================

:WEBSITE (original, pyGtk):  http://projects.flogisoft.com/alsa-tray/
:WEBSITE (new, GTK+):        https://github.com/BeniaminK/alsaTray/
:VERSION:  0.7
:RELEASED: Mon Mar 12 15:57:39 CET 2018

ALSA Tray Provides a systray icon and a command line interface for
setting the volume of the ALSA Mixers.

**Dependencies:**
 * [Needed  ] pyAlsaAudio <http://pyalsaaudio.sourceforge.net/>

 * [Optional] Python XDG <http://freedesktop.org/wiki/Software/pyxdg>
                NOTE: Used for finding the best place for the
                config file.

 * [Optional] Python GTK+ 3<https://python-gtk-3-tutorial.readthedocs.io/en/latest/>
                NOTE: Python GTK+ 3 is optional for using ALSA Tray with CLI, but
                it is needed for having a systray icon.

 * [Optional] DBus Python <http://cgit.freedesktop.org/dbus/dbus-python/>
                NOTE: Needed for the support of multimedia keys.

 * [Optional] HAL <http://www.freedesktop.org/wiki/Software/hal>
                NOTE: Needed for the support of multimedia keys.

 * [Optional] pyNotify <http://www.galago-project.org/>
                 NOTE: Needed for the notifications.

**Building dependencies:**
 * [Optional] GNU gettext <http://www.gnu.org/software/gettext/>

**Usage**
 run 'alsa-tray' for launching ALSA Tray in systray

 run 'alsa-tray --help' or 'man alsa-tray' for help with CLI otions

**Install**
 For install ALSA Tray, run 'python setup.py install'

**Uninstall**
 For uninstall ALSA Tray, run 'pip uninstall ALSATray'

