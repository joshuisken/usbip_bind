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

### kernel configuration
Use <kbd>dwc2</kbd> instead of <kbd>otg_dwc</kbd>

On the raspberry, add the following line to <kbd>/boot/config</kbd> 

    dtoverlay=dwc2

Also add the folowing option to the kernel cmdline in
<kbd>/boot/cmdline.txt</kbd> 

    modules-load=dwc2

That will replace the <kbd>dwc-otg</kbd> driver by <kbd>dwc2</kbd>,
since the <kbd>dwc-otg</kbd> does not work at this time.

### Installation

The directories <kbd>systemd</kbd> and <kbd>udev</kbd> can be rsync-ed
to the server to provide the udev rules and the systemd services.

The kernel configuration needs to be done by hand.


##  Client configuration

On the client you can find what USB devices are exported from the
server using <kbd>usbip</kbd>

    $ usbip list -r <server>

Then you can attach a USB device with

    $ usbip attach -r <server> -b <busid>

With <kbd><busip></kbd> for example being <kbd>1-1.2.1</kbd>, i.e. the
busid on the server.  Using <kbd>usbview</kbd> you can find a
<kbd>USB/IP Virtual Host Controller</kbd> under which the attached USB
devices can be found. There exist default 2 controller, one for USB2
and one for USB3, i.e. 480Mb/s and 5GB/s. Each virtual host controller
allows for maximal eight attached devices.


### kernel configuration
Often, having 8 virtual USB devices is not sufficient. One would like
to increase the number of devices which can be attached at the same
time.
Sadly, the kernel module in which the max number of devices is defined
can only be re-configured at compile time. I.e. a module parameter to
dynamically extend the amount of devices does not exist at this time.

Therefore, the kernel module <kbd>vhci_hcd</kbd> needs to be
recompiled to increase the maximum number of virtual USB devices. Two
variables are used for this:

    CONFIG_USBIP_VHCI_HC_PORTS=10
    CONFIG_USBIP_VHCI_NR_HCS=2

The first increases the maximum number of devices to 10 for a virtual
host controller. With the second parameters one can increase the
number of host controllers. Filling in 2 means here that in total 4
virtual host controllers are created, 2 for 480Mb/s and 2 for 5Gb/s.

Bear in mind that possibly in other parts of the kernel the amount of
USB devices is limited as well: I did not investigate this further.

### Installation

If needed the kernel module re-compilation needs to be done by
hand. Further no extras need to be installed.

## Intel/Altera FPGA boards

On Altera boards the default device id for a JTAG-blaster is
<kbd>09fb:6810</kbd>. This is the situation when the board is powered
up. However, when you start the <kbd>jtagd</kbd> using
<kbd>jtagconfig</kbd> the device is being re-programmed and turned
into a device with id <kbd>09fb:6010</kbd>.

This **kills the usbip connection**.

So after starting the <kbd>jtagd</kbd> one has to re-attach the USB
device as describe above. This operation needs be to repeated after
the FPGA board went through a power cycle.
The modified device seems to have become a dual uart of which one is
used for the JTAG programmer.

## Automating things

As inital step a python script in <kbd>scripts</kbd> helps in
performing the attachement of USB devices which needs to be extende to
become more easily usable. 

In this script a number of devices and the server are predefined, this
needs to be done using an <kbd>.ini</kbd> file or similar.

