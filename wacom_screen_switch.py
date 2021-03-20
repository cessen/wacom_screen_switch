#!/usr/bin/env python3

""" A simple script that cycles your wacom device through the various screens
    in a multi-monitor setup.  It is meant to be hooked up to a hot key, for
    example, to allow the user to quickly navigate between screens.

    It requires both xsetwacom and xrandr to be installed.
"""

import os
import os.path
import time
import signal
import subprocess
import tempfile


# The signal to use for communication between processes
mysig = signal.SIGRTMIN + 1
if mysig > signal.SIGRTMAX:
	exit(1)

pid = str(os.getpid())
pidfile = tempfile.gettempdir() + "/" + "tmp_wacom_screen_switch_pid.pid"
screen_device_names = []
wacom_device_names = []
screen_device_index = -1


def get_wacom_device_names():
    """ Returns a list of wacom device names from xsetwacom.
    """
    proc = subprocess.Popen(["xsetwacom", "--list", "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    proc.wait()
    lines = out.decode("utf-8").split("\n")

    devices = []
    for line in lines:
        if "id:" in line:
            dev, tail = line.split("id:", 1)
            devices += [dev.strip()]
    return devices


def test_screen_names(screen_names):
    """ Test whether xsetwacom accepts the given screen names for device switching.
        Returns True if all the screen names work.  Returns false if any of them fail.
    """
    dev_names = get_wacom_device_names()
    for sname in screen_names:
        for dev in dev_names:
            proc = subprocess.Popen(["xsetwacom", "--set", dev, "MapToOutput", sname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            proc.wait()
            lines = str(out).split("\n") + str(err).split("\n")
            for l in lines:
                if "Unable to find an output" in l:
                    return False
    return True


def get_screen_device_names():
    """ Returns a list of connected screen device names from xrandr.
    """
    proc = subprocess.Popen("xrandr", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    proc.wait()
    lines = out.decode("utf-8").split("\n")

    devices = []
    for line in lines:
        if "connected" in line and "disconnected" not in line:
            dev, tail = line.split(" ", 1)
            devices += [dev.strip()]

    if test_screen_names(devices):
        # The screen devices work, so use as-is.
        return devices
    else:
        # The devices don't work, so it's probably nvidia.
        # Substitute in "HEAD-0", "HEAD-1", etc.
        nv_devices = []
        for i in range(len(devices)):
            nv_devices += ["HEAD-" + str(i)]
        return nv_devices


def cycle_screen(sig, stack):
    # Ignore further signals while working
    signal.signal(mysig, signal.SIG_IGN)

    global screen_device_index
    screen_device_index = (screen_device_index + 1) % len(screen_device_names)

    sdev = screen_device_names[screen_device_index]
    for dev in wacom_device_names:
        subprocess.Popen(["xsetwacom", "--set", dev, "MapToOutput", sdev]).wait()

    # Watch for signals again
    signal.signal(mysig, cycle_screen)


def cleanup_and_exit(sig, stack):
    print("Cleaning up and exiting.")
    os.remove(pidfile)
    exit(0)


def main_loop():
    global screen_device_names
    global wacom_device_names
    global screen_device_index

    # Get screen and wacom device names
    screen_device_names = get_screen_device_names()
    wacom_device_names = get_wacom_device_names()

    # Set wacom devices to first screen
    screen_device_index = -1
    cycle_screen(None, None)

    # Set up screen switch signal
    signal.signal(mysig, cycle_screen)
    with open(pidfile, "w") as f:
        f.write(pid)
        f.flush()

    # Set up exit signals
    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGHUP, cleanup_and_exit)
    signal.signal(signal.SIGQUIT, cleanup_and_exit)
    signal.signal(signal.SIGABRT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)

    # Sit and wait for signals
    while True:
        time.sleep(60) # Arbitrary number of seconds - will be interrupted by caught signal

        # Check to make sure the pidfile still exists
        # and still represents this process.  This ensures
        # that this process doesn't keep running indefinitely
        # even after it become useless.
        try:
            f = open(pidfile, "r")
        except:
            exit(1)
        finally:
            fpid = f.readline().strip()
            if fpid != pid:
                exit(1)


if __name__ == "__main__":
    if os.path.exists(pidfile):
        # If the main process already appears to be running,
        # send it a signal to switch screens.
        with open(pidfile, "r") as f:
            fpid = int(f.readline().strip())
        try:
            os.kill(fpid, mysig)
            print("Already started!  Switch signal sent.")
        except OSError:
            # If it turns out the main process isn't actually running,
            # start this as the main process
            main_loop()
    else:
        main_loop()


