#!/usr/bin/python

class NetconfigException(Exception):
    m_msg = ''
    def __init__(self, msg):
        self.m_msg = msg
    def what(self):
        return m_msg
