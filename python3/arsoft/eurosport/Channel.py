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
    def is_now(self):
        now = datetime.datetime.now()
        return True if now < self.endtime and now >= self.starttime else False


class Channel:

    data = {}

    playlist = None

    def __init__(self, data_array):
        if 'channellivelabel' not in data_array or 'livestreams' not in data_array:
            raise Channel.InvalidData("Could not get stream information")
        self.data = data_array
        self._schedules = None

    def __str__(self):
        return self.name

    @property
    def name(self):
        return self.data['channellivelabel']

    @property
    def stream_url(self):
        return self.data['livestreams'][0]['securedurl']

    @property
    def catchup_stream_url(self):
        if 'catchupstreams' in self.data:
            return self.data['catchupstreams'][0]['url']
        else:
            return None

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

    def download_playlist(self, timeoffset=None):
        if self.stream_url is None:
            raise Channel.NoLiveStream
        self.playlist = Playlist(self.stream_url, timeoffset=timeoffset)

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
            if sched.is_now:
                return sched
        return None

    class InvalidData(Exception):
        pass

    class NoLiveStream(Exception):
        pass
