#!/usr/bin/python

import string
import os
import urllib
import rfc822
import time

# simple python script for extracting mostly used types of archives
# this script extracts .tar, .tar.gz, .tar.bz2, .gz and .zip archives 
#
def unpack(filename, target=None, files=''):
    if target is None:
        target = os.getcwd()
    if (filename.find('.tar.gz') != -1):                           #       function. It takes string
        os.system("tar -C " + target + " -xzf " + filename + ' ' + files + ' 2>&1 > /dev/null')             #   filename as argument.
    elif (filename.find('.tar.bz2') != -1):                        #       functon than calls 
        os.system("tar -C " + target + " -xjf " + filename + ' ' + files + ' 2>&1 > /dev/null')             #   appropriate command according
    elif (filename.find('.tar') != -1):                            #       to file extension
        os.system("tar -C " + target + " -xf " + filename + ' ' + files +  ' 2>&1 > /dev/null')
    elif (filename.find('.gz') != -1):
        os.system("gunzip -c " + filename + " > " + target)
    elif (filename.find('.zip') != -1):            
        os.system("unzip -d " + target + " " + filename + ' 2>&1 > /dev/null')
    elif (filename.find('.deb') != -1):
        #print "ar -p " + filename + ' data.tar.gz | tar xz -C ' + target + ' ' + files + ' 2>&1 > /dev/null'
        os.system("ar -p " + filename + ' data.tar.gz | tar xz -C ' + target + ' ' + files + ' 2>&1 > /dev/null')
    else: 
        print "Wrong archive or filename"         # other types not supported

def createpath(path):
    e = path.split('/')
    for i in range(0, len(e)):
        p = string.join(e[0:i + 1], '/')
        if p == '':
            continue
        if not os.path.exists(p):
            os.mkdir(p)


def retrieve_file(url, localfile):
    f = urllib.urlopen(url)
    tmp = f.info()
    f.close()
    #print tmp
    #print tmp['Last-Modified']
    modified = time.mktime(rfc822.parsedate(tmp['Last-Modified']))
    if tmp.has_key('Content-Length'):
        size = int(tmp['Content-Length'])
    else:
        size = 0
    if os.path.exists(localfile):
        localmodified = os.path.getmtime(localfile)
        localsize = os.path.getsize(localfile)
    else:
        localmodified = 0
        localsize = -1
    if modified > localmodified or size != localsize:
        urllib.urlretrieve(url, localfile)
    return True

def qsort(L):
    if len(L) <= 1: return L
    return qsort( [ lt for lt in L[1:] if lt < L[0] ] )  +  [ L[0] ]  +  qsort( [ ge for ge in L[1:] if ge >= L[0] ] )

def sortdict(d):
    r = []
    for k in qsort(d.keys()):
        r.append(d[k])
    return r
