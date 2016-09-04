#!/usr/bin/python3
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
#
# Original from https://github.com/glothriel/libeurosport

import arsoft.m3u8 as m3u8
import urllib.request, urllib.error
import time
import threading
from collections import deque


class Stream:

    def __init__(self, stream_config, cookie):
        self.m3u_list = None
        self.uri = None
        self.stream_config = None
        self.parent_cookie = None
        self.my_cookie = None
        self.uri = stream_config.absolute_uri
        self.parent_cookie = cookie
        self.stream_config = stream_config
        self.request_for_options()

    def request_for_options(self):
        try:
            api_call = urllib.request.Request(self.uri, headers={'Cookie': self.parent_cookie})
            contents = urllib.request.urlopen(api_call)
            self.m3u_list = m3u8.loads(contents.read().decode('utf-8'))
            self.m3u_list.base_uri = self.uri[:self.uri.rfind('/')]
            if len(self.m3u_list.files) == 0:
                raise Stream.NoStreamPartsFound
        except urllib.error.HTTPError:
            print('Http error on ' + self.uri)
        pass

    def get_stream_url(self):
        return self.m3u_list.base_uri + '/' + self.m3u_list.files[0]

    @property
    def url(self):
        return self.get_stream_url()

    @property
    def stream_info(self):
        return self.stream_config.stream_info

    @property
    def bandwidth(self):
        return self.get_available_bandwidth()

    def get_part(self):
        url = self.get_stream_url()
        api_call = urllib.request.Request(url, headers={'Cookie': self.parent_cookie})
        contents = urllib.request.urlopen(api_call)
        return contents.read()


    def get_available_bandwidth(self):
        return self.stream_config.stream_info[0]

    @staticmethod
    def is_url_audio_only(url):
        return 'audio' in url

    class BandwidthNotAvailable(Exception):
        pass

    class NoStreamPartsFound(Exception):
        pass


class StreamDownloader(object):

    def __init__(self, stream):
        self.downloaded_parts = {}
        self.stream = None
        self.parts_to_be_played = deque([])
        self.stream = stream
        self._stop = False
        threading.Thread(target=self.play).start()
        pass

    def play(self):
        while not self._stop:
            try:
                if self.stream.get_stream_url() in self.downloaded_parts:
                    self.stream.request_for_options()
                    time.sleep(1)
                    continue
                else:
                    print('Downloading part ' + self.stream.get_stream_url())
                    self.downloaded_parts[self.stream.get_stream_url()] = True
                    self.parts_to_be_played.append(self.stream.get_part())
            except KeyboardInterrupt:
                self._stop = True

    def stop(self):
        self._stop = True

    def get_next_part(self):
        if len(self.parts_to_be_played) == 0:
            raise StreamDownloader.NoDataAvailable
        else:
            return self.parts_to_be_played.popleft()

    class NoDataAvailable(Exception):
        pass


