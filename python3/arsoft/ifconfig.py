#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

"""from http://twistedmatrix.com/wiki/python/IfConfig
"""

import socket
import errno
import array
import fcntl
import struct
import platform
from logging import debug, info, exception, error, warning, handlers

class ifconfig (object):
    """Access to socket interfaces"""

    SIOCGIFNAME = 0x8910
    SIOCGIFCONF = 0x8912
    SIOCGIFFLAGS = 0x8913
    SIOCGIFADDR = 0x8915
    SIOCGIFBRDADDR = 0x8919
    SIOCGIFNETMASK = 0x891b
    SIOCGIFHWADDR = 0x8927
    SIOCGIFCOUNT = 0x8938

    IFF_UP = 0x1                # Interface is up.
    IFF_BROADCAST = 0x2         # Broadcast address valid.
    IFF_DEBUG = 0x4             # Turn on debugging.
    IFF_LOOPBACK = 0x8          # Is a loopback net.
    IFF_POINTOPOINT = 0x10      # Interface is point-to-point link.
    IFF_NOTRAILERS = 0x20       # Avoid use of trailers.
    IFF_RUNNING = 0x40          # Resources allocated.
    IFF_NOARP = 0x80            # No address resolution protocol.
    IFF_PROMISC = 0x100         # Receive all packets.
    IFF_ALLMULTI = 0x200        # Receive all multicast packets.
    IFF_MASTER = 0x400          # Master of a load balancer.
    IFF_SLAVE = 0x800           # Slave of a load balancer.
    IFF_MULTICAST = 0x1000      # Supports multicast.
    IFF_PORTSEL = 0x2000        # Can set media type.
    IFF_AUTOMEDIA = 0x4000      # Auto media select active.

    def __init__ (self):
        # create a socket so we have a handle to query
        self.sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _ioctl (self, func, args):
        return fcntl.ioctl(self.sockfd.fileno(), func, args)

    def _getaddr (self, ifname, func):
        ifreq = struct.pack("32s", ifname)
        try:
            result = self._ioctl(func, ifreq)
        except IOError as msg:
            warning("error getting addr for interface %r: %s", ifname, msg)
            return None
        return socket.inet_ntoa(result[20:24])

    def getInterfaceList (self):
        """
        Get all interface names in a list.
        """
        # initial 8kB buffer to hold interface data
        bufsize = 8192
        # 80kB buffer should be enough for most boxen
        max_bufsize = bufsize * 10
        while True:
            buf = array.array('c', '\0' * bufsize)
            ifreq = struct.pack("iP", buf.buffer_info()[1], buf.buffer_info()[0])
            try:
                result = self._ioctl(self.SIOCGIFCONF, ifreq)
                break
            except IOError as msg:
                # in case of EINVAL the buffer size was too small
                if msg[0] != errno.EINVAL or bufsize == max_bufsize:
                    raise
            # increase buffer
            bufsize += 8192
            
        arch = platform.architecture()[0]
        if arch == '32bit':
            ifreq_size = 32
        elif arch == '64bit':
            ifreq_size = 40
        else:
            raise OSError("Unknown architecture: %s" % arch)

        # loop over interface names
        data = buf.tostring()
        iflist = {}
        size, ptr = struct.unpack("iP", result)
        i = 0
        
        while i < size:
            # XXX on *BSD, struct ifreq is not hardcoded 32, but dynamic.
            ifconf = data[i:i+ifreq_size]
            
            name = ifconf[0:16].split('\0', 1)[0]
            ip   = socket.inet_ntoa(ifconf[20:24])
            
            #name, dummy = struct.unpack("16s24s", ifconf)
            #name, dummy = name.split('\0', 1)
            debug("found interface " + name + " ip=" + str(ip) )
            if name in iflist:
                iflist[name].append(ip)
            else:
                iflist[name] = [ip]
            i += ifreq_size
        return iflist

    def getFlags (self, ifname):
        """
        Get the flags for an interface
        """
        ifreq = struct.pack("32s", ifname)
        try:
            result = self._ioctl(self.SIOCGIFFLAGS, ifreq)
        except IOError as msg:
            warning("error getting flags for interface " + ifname + ": " + str(msg))
            return 0
        # extract the interface's flags from the return value
        flags, = struct.unpack('H', result[16:18])
        # return "UP" bit
        return flags

    def getAddr (self, ifname):
        """
        Get the inet addr for an interface.
        @param ifname: interface name
        @type ifname: string
        """
        return self._getaddr(ifname, self.SIOCGIFADDR)

    def getNetmask (self, ifname):
        """
        Get the netmask for an interface.
        @param ifname: interface name
        @type ifname: string
        """
        return self._getaddr(ifname, self.SIOCGIFNETMASK)

    def getBroadcast (self, ifname):
        """
        Get the broadcast addr for an interface.
        @param ifname: interface name
        @type ifname: string
        """
        return self._getaddr(ifname, self.SIOCGIFBRDADDR)

    def getHWAddress(self, ifname):
        """
        Get the hardware addr for an interface.
        @param ifname: interface name
        @type ifname: string
        """
        ifreq = struct.pack("32s", ifname)
        try:
            result = self._ioctl(self.SIOCGIFHWADDR, ifreq)
        except IOError as msg:
            warning("error getting addr for interface " + ifname + ": " + str(msg))
            return None
        hwaddr=[]
        for char in result[18:24]: 
            hwaddr.append("%02X" % ord(char))
        return ':'.join(hwaddr)

    def isUp (self, ifname):
        """
        Check whether interface is UP.
        @param ifname: interface name
        @type ifname: string
        """
        return (self.getFlags(ifname) & self.IFF_UP) != 0

    def isLoopback (self, ifname):
        """
        Check whether interface is a loopback device.
        @param ifname: interface name
        @type ifname: string
        """
        # since not all systems have IFF_LOOPBACK as a flag defined,
        # the ifname is tested first
        if ifname == 'lo':
            return True
        return (self.getFlags(ifname) & self.IFF_LOOPBACK) != 0
    
    def getList(self):
        ret = []
        interfaces = self.getInterfaceList()
        for (ifname, ipaddr_list) in list(interfaces.items()):
            if self.isLoopback(ifname) == False:
                netmask = self.getNetmask(ifname)
                broadcast = self.getBroadcast(ifname)
                hwaddr = self.getHWAddress(ifname)
                iface = {'name':ifname, 'addr':ipaddr_list, 'netmask':netmask, 'broadcast':broadcast, 'hwaddr':hwaddr }
                debug("got interface " + str(iface))
                ret.append(iface)
        return ret
