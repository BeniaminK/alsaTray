#!/bin/bash

#Installation script for ALSA Tray

_install() {
	#Install
	#$1 : the output path, if different of /
	#Code
	mkdir -pv "$1"/usr/bin
	cp -v ./code/alsa_tray.py "$1"/usr/bin/alsa-tray
	chmod -v 755 "$1"/usr/bin/alsa-tray
	#Share
	mkdir -pv "$1"/usr/share/alsa-tray/
	cp -v ./pixmaps/* "$1"/usr/share/alsa-tray/
	#doc
	mkdir -pv "$1"/usr/share/doc/alsa-tray/
	cp -v README "$1"/usr/share/doc/alsa-tray/
	cp -v AUTHORS "$1"/usr/share/doc/alsa-tray/
	#man
	mkdir -pv "$1"/usr/share/man/man1/
	cp -v ./man.1 "$1"/usr/share/man/man1/alsa-tray.1
	gzip --best -f "$1"/usr/share/man/man1/alsa-tray.1
}


_remove() {
	#Remove ALSA Tray
	rm -rv /usr/share/alsa-tray
	rm -rv /usr/share/doc/alsa-tray
	rm -v /usr/bin/alsa-tray
	rm -v /usr/share/man/man1/alsa-tray.1.gz
}


#Force english
export LANG=c
#Go to the scrip directory
cd "${0%/*}" 1> /dev/null 2> /dev/null

#Head text
echo "ALSA Tray - Set the volume of the ALSA Master mixer."
echo

#Action do to
if [ "$1" == "--install" ] || [ "$1" == "-i" ] ; then {
	echo "Installing ALSA Tray..."
	if [ "$(whoami)" == "root" ] ; then {
		_install
	} else {
		echo "E: Need to be root"
		exit 1
	} fi
} elif [ "$1" == "--package" ] || [ "$1" == "-p" ] ; then {
	echo "Packaging ALSA Tray..."
	if [ -d "$2" ] ; then {
		_install "$2"
	} else {
		echo "E: '$2' is not a directory"
		exit 2
	} fi
} elif [ "$1" == "--remove" ] || [ "$1" == "-r" ] ; then {
	echo "Removing ALSA Tray..."
	if [ "$(whoami)" == "root" ] ; then {
		_remove
	} else {
		echo "E: Need to be root"
		exit 1
	} fi
} else {
	echo "Arguments :"
	echo "  --install : install ALSA Tray on your computer."
	echo "  --package <path> : install ALSA Tray in <path> (Useful for packaging)."
	echo "  --remove : remove ALSA Tray from your computer."
} fi

exit 0


