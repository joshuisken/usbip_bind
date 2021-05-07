#! /home/huisken/local/python/3.9.4/bin/python3
import argparse
import subprocess
import sys

usb_bus_ids = {
    '1-1.2.1':   ('0403:6010', 'zynq-p2', '1234-tul'),

    '1-1.2.4.3': ('0403:6010', 'nexus?', '210276A792DF'),

    '1-1.3.1.4': ('09fb:6810', 'DE-SoC', 'DE-SoC-003-08717'),
    '1-1.2.4.4': ('0403:6001', 'DE0SoC', 'A503XQ5M'),

    '1-1.3.1.2': ('09fb:6810', 'DE-SoC', 'DE-SoC-003-18470'),
    '1-1.3.1.1': ('0403:6001', 'DE0SoC Paul', 'A107T4DK', 'broken?'),

    '1-1.3.2':   ('09fb:6810', 'DE-SoC', 'DE-SoC-006-00660'),
    '1-1.3.3':   ('0403:6001', 'DE10SoC', 'A106I60D', '4.1.33-rt38...', 'Angstrom 2015.12', 'de10soc'),

    '1-1.3.4.1': ('09fb:6810', 'USB-BlasterII', '5CSXSoC0050405'),
    '1-1.3.4.2': ('0403:6001', 'C5SoC', 'A101YYR5', '4.14.73-ltsi', 'Angstrom 2018.06', 'c5soc'),

    '1-1.3.4.3': ('09fb:6810', 'DE-SoC', 'DE-SoC-001-02323'),
    '1-1.3.4.4': ('0403:6001', 'DE1SoC Kamlesh', 'A801SB9B', '4.1.33-rt38..', 'Angstrom 2018.06', 'brnwv1-de1'),
}

def usbip_cmd_all(cmd):
    jtag = []
    for b, i in usb_bus_ids.items():
        print(" ".join(cmd + [b]))
        subprocess.run(cmd + [b])
        if i[0] == '09fb:6810':
            jtag.append(b)
    return jtag

def usbip_cmd(cmd, busids):
    for b in busids:
        print(" ".join(cmd + [b]))
        subprocess.run(cmd + [b])

def args_parse():
    parser = argparse.ArgumentParser(
        description='Bind USB devices'
    )
    parser.add_argument(
        '--detach', '-d', action='store_true',
        help='Detach all USBIP devices.'
    )
    parser.add_argument(
        '--jtag', '-j', action='store_true',
        help='Select only Intel/Altera JTAG devices.'
    )
    parser.add_argument(
        '--list-remote', '-l', dest='listremote', action='store_true',
        help='List available remote USB devices.'
    )
    args = parser.parse_args()
    return args

def detach():
    'Detach all devices, need to scan for port number'
    cmd = ['sudo', 'usbip', 'port']
    # Find all ports
    u = subprocess.run(cmd, capture_output=True)

    # Fetch port IDs from stdout
    print(str(u.stdout))
    used_ports = []
    cmd = ['sudo', 'usbip', 'detach', '-p']
    for p in used_ports:
        subprocess.run(cmd + [p])
    return 0

def list_usb():
    cmd = ['sudo', 'usbip', 'list', '-r', 'rbusb']
    subprocess.run(cmd)
    return 0

def main():
    args = args_parse()
    cmd = ['sudo', 'usbip', 'attach', '-r', 'rbusb', '-b']
    if args.detach:
        return detach()
    if args.listremote:
        return list_usb()
    if args.jtag:
        jtag = []
        for b, i in usb_bus_ids.items():
            if i[0] == '09fb:6810':
                jtag.append(b)            
        return usbip_cmd(cmd, jtag)
    else:
        return usbip_cmd(cmd, usb_bus_ids.keys())
    return 0

if __name__ == "__main__":
    sys.exit(main())
