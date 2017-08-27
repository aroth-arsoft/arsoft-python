#!/usr/bin/python3
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
#
# Original from https://github.com/glothriel/libeurosport

import arsoft.m3u8 as m3u8
import urllib.request
from .Stream import Stream


class Playlist:

    def __init__(self, uri, timeoffset=None, client=None, token=None):
        self.m3u_list = None
        self.token = token
        self.cookie = None
        self.client = client
        self.base_uri = None
        self.active_stream = None
        self.streams = []
        #self.m3u_list = m3u8.load(uri)
        self.download_list(uri)

    def download_list(self, uri):
        print('Playlist.download_list %s' % uri)
        req = urllib.request.Request(uri, headers={'Cookie': 'authorization=%s'%self.token})
        contents = urllib.request.urlopen(req)
        self.set_base_uri(uri)
        self.m3u_list = m3u8.M3U8(contents.read().decode('utf8'), base_uri=self.base_uri)
        self.cookie = contents.getheader('Set-Cookie')
        self.create_streams()

    def set_base_uri(self, uri):

        self.base_uri = uri[:uri.rfind('/')]
        print('set_base_uri %s -> %s' % (uri, self.base_uri))

    def create_streams(self):
        for s in self.m3u_list.playlists:
            if Stream.is_url_audio_only(s.absolute_uri):
                continue
            try:
                self.streams.append(Stream(s, self.token))
            except Stream.NoStreamPartsFound:
                continue
        if len(self.streams) > 0:
            self.active_stream = self.streams[0]

    def get_available_bandwidths(self):
        return sorted([stream.get_available_bandwidth() for stream in self.streams])

    def set_bandwidth(self, desired):
        print('set_bandwidth %s' % desired)
        found = False
        if desired is None:
            for stream in self.streams:
                if self.active_stream is None or stream.get_available_bandwidth() > self.active_stream.get_available_bandwidth():
                    self.active_stream = stream
                    print('set_bandwidth select max %s' % stream.get_available_bandwidth())
                    found = True
        else:
            current_diff = 1e10
            for stream in self.streams:
                if stream.get_available_bandwidth() <= desired:
                    stream_diff = desired - stream.get_available_bandwidth()
                    if self.active_stream is None:
                        self.active_stream = stream
                        diff = desired - self.active_stream.get_available_bandwidth()
                        print('set_bandwidth select %s' % stream.get_available_bandwidth())
                        found = True
                    elif stream_diff < current_diff:
                        self.active_stream = stream
                        current_diff = desired - self.active_stream.get_available_bandwidth()
                        print('set_bandwidth select better %s' % stream.get_available_bandwidth())
                        found = True
        if not found:
            raise Stream.BandwidthNotAvailable

    def get_active_stream_url(self):
        if self.active_stream:
            return self.active_stream.get_stream_url()
        else:
            raise Playlist.NoStreamSelected

    class NoStreamSelected(Exception):
        pass




