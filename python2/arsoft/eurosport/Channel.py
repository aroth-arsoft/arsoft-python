#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
#
# Original from https://github.com/glothriel/libeurosport

from .Playlist import Playlist

class Channel:

    data = {}

    playlist = None

    def __init__(self, data_array):
        if 'channellivelabel' not in data_array or 'livestreams' not in data_array:
            raise Channel.InvalidData("Could not get stream information")
        self.data = data_array

    def __str__(self):
        return self.name

    @property
    def name(self):
        return self.data['channellivelabel']

    @property
    def stream_url(self):
        return self.data['livestreams'][0]['securedurl']

    @property
    def active_stream(self):
        return self.playlist.active_stream

    @property
    def streams(self):
        return self.playlist.streams

    def get_active_stream_url(self):
        return self.playlist.get_active_stream_url()

    def get_available_quality_options(self):
        return self.playlist.get_available_bandwidths()

    def set_quality(self, desired):
        return self.playlist.set_bandwidth(desired)

    def download_playlist(self):
        self.playlist = Playlist(self.stream_url)

    class InvalidData(Exception):
        pass
