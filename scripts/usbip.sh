#! /bin/sh

SRV=rbusb

BUSIDS='
  1-1.3.4.4
  1-1.3.4.3
  1-1.3.4.2
  1-1.3.4.1
  1-1.3.3
  1-1.3.2
  1-1.3.1.4
  1-1.3.1.2
  1-1.3.1.1
  1-1.2.4.4
  1-1.2.4.3           
  1-1.2.1
'

for b in ${BUSIDS}
do
    sudo usbip attach -r ${SRV} -b ${b}
done
