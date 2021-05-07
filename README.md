# Setting up USBIP

The idea is to connect FPGA boards using USB to a raspberry.

The raspberry provides the USB devices using USBIP to a client.

We have the following components on the server (raspberry):
- udev rules to enable provision of specific device over usbip
- systemd config files 
- kernel configuration: default <kbd>dwc-otg</kbd> module crashes and
  needs to be replaced by <kbd>dwc2</kbd>

For the client we have:
- a python script to drive uspip for a set of devices
- a recompilation/reconfiguration of the vhci-hcd kernel module 
  since it provides too few USB virtual devices

## Server configuration
### udev rules
Configuring a usb device while the the server is running is different
as compared to booting the server while the devices are already
connected. The udev rules are invoked early in the boot process while
the usbip daemon is required to provide IP access to the usb device.
In fact <kbd>systemd-udevd.service</kbd> is started well before
<kbd>usbipd.service</kbd>. 

So, a rule like

    SUBSYSTEM=="usb" ATTR{idVendor}=="0403" ATTR{idProduct}=="6001" \
        ACTION=="add" \
		RUN+="/usr/bin/usbip bind -b $KERNEL"

fails since the usbip daemon is not yet started. To avoid possible
dependency issues I decided to postpone the usb binding process using
systemd. 

Instead, such a rule is now formulated as:

    SUBSYSTEM=="usb" ATTR{idVendor}=="0403" ATTR{idProduct}=="6001" \
		ACTION=="add" \
        TAG+="systemd" ENV{SYSTEMD_WANTS}+="usbip-bind@%k.service"

Please note the following:
- before <kbd>usbip bind</kbd> one needs to start <kbd>usbipd</kbd> to
  service the request.
- for the USB device use <kbd>ATTR</kbd> and *not* <kbd>ATTRS</kbd>
  for <kbd>idVendor</kbd> and
  <kbd>idProduct</kbd> to avoid multiple invocations of the udev rule
- <kbd>TAG+="systemd"</kbd> is required to enable
  <kbd>SYSTEMD_WANTS</kbd> correctly.

### systemd services
As a consequence we need to define two systemd services. The first one
is <kbd>usbipd.service</kbd> to provide the USB devices over IP. It
only starts the <kbd>usbipd</kbd> daemon after the network is
available (which actually might only occur after completing
<kbd>systemd-udev.service</kbd>). 

The second service is a template service named
<kbd>usbip-bind@.service</kbd>. This is invoked using the udev rule
above using the variable <kbd>SYSTEMD_WANTS</kbd>.
In this second service there exists a dependency that is only starts
after <kbd>usbipd.service</kbd> has been started. Effectively delaying
the binding of the USB device.

##  Client configuration

