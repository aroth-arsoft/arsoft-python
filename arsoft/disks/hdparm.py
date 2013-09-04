#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from arsoft.utils import runcmdAndGetData

class HdParm(object):
    def __init__(self, device=None, hdparm_executeable='/sbin/hdparm', verbose=False):
        self.hdparm_executeable = hdparm_executeable
        self.device = device
        self.verbose = verbose

    def _exec(self, args):
        final_args = args
        final_args.append(self.device)
        (sts, stdoutdata, stderrdata) = runcmdAndGetData(self.hdparm_executeable, args, verbose=self.verbose)
        return (sts, stdoutdata, stderrdata)

    def __str__(self):
        ret = 'device=' + str(self.device) +\
            ''
        return ret

    def sleep(self):
        self._exec(['-Y'])

    def standby(self):
        self._exec(['-y'])

if __name__ == '__main__':
    import sys
    hd = HdParm(device=sys.argv[1], verbose=True)
    hd.standby()
