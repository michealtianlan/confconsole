# Copyright (c) 2008 Alon Swartz <alon@turnkeylinux.org> - all rights reserved

import re
import os

class Error(Exception):
    pass

class Interfaces:
    """class for controlling /etc/network/interfaces

    An error will be raised if the interfaces file does not include the
    header: # UNCONFIGURED INTERFACES (in other words, we will not override
    any customizations)
    """

    CONF_FILE='/etc/network/interfaces'

    def __init__(self):
        self.read_conf()

    @staticmethod
    def _header():
        return "\n".join(["# UNCONFIGURED INTERFACES",
                          "# remove the above line if you edit this file"])

    @staticmethod
    def _loopback():
        return "\n".join(["auto lo",
                          "iface lo inet loopback"])

    def read_conf(self):
        self.conf = {}
        self.unconfigured = False

        for line in file(self.CONF_FILE).readlines():
            line = line.rstrip()

            if line == self._header().splitlines()[0]:
                self.unconfigured = True

            if not line or line.startswith("#"):
                continue

            if line.startswith("auto") or line.startswith("ifname"):
                ifname = line.split()[1]

            if not self.conf.has_key(ifname):
                self.conf[ifname] = line + "\n"
            else:
                self.conf[ifname] = self.conf[ifname] + line + "\n"

    def write_conf(self, ifname, ifconf):
        self.read_conf()
        if not self.unconfigured:
            raise Error("not writing to %s\nheader not found: %s" %
                        (self.CONF_FILE, self._header().splitlines()[0]))

        #append legal iface options already defined
        iface_opts = ('pre-up', 'up', 'post-up', 'pre-down', 'down', 'post-down')
        for line in self.conf[ifname].splitlines():
            line = line.strip()
            if line.split()[0] in iface_opts:
                ifconf.append("    " + line)

        fh = file(self.CONF_FILE, "w")
        print >> fh, self._header() + "\n"
        print >> fh, self._loopback() + "\n"
        print >> fh, "\n".join(ifconf) + "\n"

        for c in self.conf:
            if c in ('lo', ifname):
                continue

            print >> fh, self.conf[c]

        fh.close()

    def set_dhcp(self, ifname):
        ifconf = ["auto %s" % ifname,
                  "iface %s inet dhcp" % ifname]

        self.write_conf(ifname, ifconf)

    def set_manual(self, ifname):
        ifconf = ["auto %s" % ifname,
                  "iface %s inet manual" % ifname]

        self.write_conf(ifname, ifconf)

    def set_static(self, ifname, addr, netmask, gateway=None, nameservers=[]):
        ifconf = ["auto %s" % ifname,
                  "iface %s inet static" % ifname,
                  "    address %s" % addr,
                  "    netmask %s" % netmask]

        if gateway:
            ifconf.append("    gateway %s" % gateway)

        if nameservers:
            ifconf.append("    dns-nameservers %s" % " ".join(nameservers))

        self.write_conf(ifname, ifconf)

class ConsoleConf:
    CONF_FILE="/etc/confconsole.conf"

    def _load_conf(self):
        if not os.path.exists(self.CONF_FILE):
            return

        for line in file(self.CONF_FILE).readlines():
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            op, val = re.split(r'\s+', line, 1)
            if op == 'default_nic':
                self.default_nic = val
            else:
                raise Error("illegal configuration line: " + line)

    def __init__(self):
        self.default_nic = None
        self._load_conf()

    def set_default_nic(self, ifname):
        self.default_nic = ifname

        fh = file(self.CONF_FILE, "w")
        print >> fh, "default_nic %s" % ifname
        fh.close()

