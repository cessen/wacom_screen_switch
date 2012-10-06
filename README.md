wacom_screen_switch
===================

A small script that cycles your wacom tablet between screens on a multi-monitor setup.

This script is Linux-specific and requires both xsetwacom and xrandr to be installed.

The first time the script is run, it starts a long-running process, and sets
the wacom tablet to map to the first monitor.  Subsequent runs simply signal
the long-running process to cycle to the next monitor.

The intent of the script is to be hooked up to a hotkey, via which the user
can then quickly cycle between monitors.  It is also best if the script is run
once on login as one of the user's auto-started programs, so that the
long-running process is already started and the wacom tablet already mapped.
