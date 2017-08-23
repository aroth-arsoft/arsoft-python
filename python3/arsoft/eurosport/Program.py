#!/usr/bin/python3
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
#
# Original from https://github.com/glothriel/libeurosport

from .Login import Login
from .Constants import *
from .Channel import Channel
import urllib.request
import urllib.parse
import json


class Program:

    channels = []

    @staticmethod
    def _get_all_query_parameters():
        return urllib.parse.urlencode({
            "data": Login.get_instance().get_confirmation(),
            "context": Login.get_instance().prepare_application_context()
        })

    @staticmethod
    def get_channel_list():
        base_url = BASE_PROGRAMS_PATH
        base_url += Program._get_all_query_parameters()
        raw_response = urllib.request.urlopen(base_url)
        return Program.extract_channels_from_json(raw_response.read().decode('utf8'))

    @staticmethod
    def extract_channels_from_json(json_str):
        channels = []
        data = json.loads(json_str)
        print(data)
        if data and data['PlayerObj']:
            for single_channel_data in data['PlayerObj']:
                channels.append(Channel(single_channel_data))
        return channels
