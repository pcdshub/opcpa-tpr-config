# PyDM Application Template for LCLS Photon Instruments

This is an application template with some boilerplate code for launching
pydm applications on the photon side.

Feel free to copy, start your own repo from this, and edit the code and
ui to your liking. I highly suggest you replace "appname" in every file and
filename with your desired application name.

There are two main ways to launch these pydm applications:
1. Via the `./launch.sh` script, which selects a pre-installed environment
   and invokes the pydm command. This is the normal way to make small
   applications. You can execute this script directly in the terminal.
2. Via the `__main__.py` script, which can be bundled with the application
   for use in an installed python environment. This is the normal way to
   make large applications. You can execute this script by calling `appname`
   with the package installed, or by calling `python -m appname` from the
   root directory.

The boilerplate files in this repository also contain utilities for tracking
the version of your application and for installing it via pip or conda.
