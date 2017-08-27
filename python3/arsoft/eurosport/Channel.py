#!/usr/bin/python3
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
#
# Original from https://github.com/glothriel/libeurosport

from .Playlist import Playlist
import re
import datetime

def esp_convert_date(dateString):
    date_regex = re.compile('Date\(([0-9]*?)\+([0-9]*?)\)')
    r = date_regex.search(dateString)
    (time, offset) = r.groups()
    time = int(time)
    time = time / 1000
    return datetime.datetime.fromtimestamp(time)

class Schedule(object):
    def __init__(self, data_array):
        if 'startdate' not in data_array and 'enddate' not in data_array:
            raise Channel.InvalidData("Could not get schedule information")
        self.data = data_array

    @property
    def starttime(self):
        return esp_convert_date(self.data["startdate"]["datetime"])

    @property
    def endtime(self):
        return esp_convert_date(self.data["enddate"]["datetime"])

    @property
    def name(self):
        return self.data["name"]

    @property
    def shortname(self):
        return self.data["shortname"]

    @property
    def description(self):
        return self.data["description"]

    @property
    def duration(self):
        return int(self.data["duration"])

    @property
    def transmission_type(self):
        return self.data["transmissiontypename"]

    @property
    def duration_human(self):
        d = self.duration
        if d >= 60:
            h = int(d / 60)
            m = int(d % 60)
            if m == 0:
                return '%ih' % h
            else:
                return '%ih, %i min' % (h,m)
        else:
            return '%imin' % d

    @property
    def title(self):
        if self.description:
            return '%s (%s)' % (self.name, self.description)
        else:
            return self.name

    @property
    def is_high_definition(self):
        return True if "hd" in self.data else False

    @property
    def sport(self):
        return self.data['sport']

    @property
    def is_currently_running(self):
        now = datetime.datetime.now()
        return True if now < self.endtime and now >= self.starttime else False

    @property
    def is_live_transmission(self):
        return True if "Live" in self.transmission_type else False

    @property
    def is_highlights(self):
        return True if "Highlight" in self.transmission_type else False

class Channel(object):

    class Url(object):
        def __init__(self, data):
            self.href = data['href']

        def __str__(self):
            return self.href
        @property
        def url(self):
            return self.href

    class Streams(object):
        def __init__(self, data):
            self._data = data

        def playlist(self, complete=False, slide=False):
            s = self._data.get('stream')
            if complete:
                return s.get('complete')
            elif slide:
                return s.get('slide')
            else:
                if 'slide' in s:
                    return s['slide']
                elif 'complete' in s:
                    return s['complete']
                else:
                    return None

        @property
        def token(self):
            return self._data.get('token')


    data = {}

    playlist = None

    def __init__(self, data_array, client):
        if 'titles' not in data_array or 'playbackUrls' not in data_array:
            raise Channel.InvalidData("Could not get stream information %s" % data_array.keys())
        self.data = data_array
        self._schedules = None
        self._client = client
        self._language = client.LANGUAGE
        self._title = None
        self.callsign = None
        self._urls = []
        self._streams = None
        for u in self.data['playbackUrls']:
            rel = u.get('rel')
            if rel == 'event' or rel == 'video':
                self._urls.append(Channel.Url(u))
            else:
                print('skip URL %s' % u)
        if 'channel' in self.data:
            self.callsign = self.data['channel'].get('callsign')
        for t in data_array['titles']:
            if t['language'] == self._language:
                self._title = t

    def __str__(self):
        return self.name

    @property
    def name(self):
        if self._title is None:
            return None
        return self._title['title'].strip()
    @property
    def description(self):
        if self._title is None:
            return None
        return self._title['description'].strip()

    @property
    def streams(self):
        if self._streams is None:
            data = self._client.streams(self._urls[0].url)
            self._streams = Channel.Streams(data)
        return self._streams

    @property
    def urls(self):
        return self._urls

    @property
    def catchup_stream_url(self):
        if 'catchupstreams' in self.data:
            return self.data['catchupstreams'][0]['url']
        else:
            return None

    @property
    def active_stream(self):
        return self.playlist.active_stream

    def get_active_stream_url(self):
        return self.playlist.get_active_stream_url()

    def get_available_quality_options(self):
        return self.playlist.get_available_bandwidths()

    def set_quality(self, desired):
        print('set_quality %s' % desired)
        return self.playlist.set_bandwidth(desired)

    def download_playlist(self, timeoffset=None):
        streams = self.streams
        if streams is None:
            raise Channel.NoLiveStream

        self.playlist = Playlist(streams.playlist(), timeoffset=timeoffset, client=self._client, token=streams.token)

    @property
    def schedules(self):
        if self._schedules is None:
            tmp_schedules = []
            if self.data["tvschedules"]:
                for s in self.data["tvschedules"]:
                    sched = Schedule(s)
                    tmp_schedules.append(sched)
            elif self.data["tvscheduleliveevents"]:
                for s in self.data["tvscheduleliveevents"]:
                    sched = Schedule(s)
                    tmp_schedules.append(sched)
            self._schedules = sorted(tmp_schedules, key=lambda s: s.starttime)
        return self._schedules

    def find_current_show(self):
        for sched in self.schedules:
            if sched.is_currently_running:
                return sched
        return None

    class InvalidData(Exception):
        pass

    class NoLiveStream(Exception):
        pass

    class NoCatchupStream(Exception):
        pass
