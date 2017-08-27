#!/usr/bin/python3
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;
#
import requests
from .Constants import *
from .Channel import *

class Client:

    class SearchError(Exception):
        def __init__(self, msg, location):
            self._msg = msg
            self._location = location
        def __str__(self):
            if self._location:
                column = self._location['column']
                line = self._location['line']
                loc = '%i, %i' % (line, column)
            else:
                loc = 'Unknown'
            return 'SearchError: %s at %s' % (self._msg, loc)

    def __init__(self, config):

        self.credentials = config.credentials
        self.IDENTITY_URL = BASE_GLOBAL_API + 'v2/user/identity'
        self.USER_URL = BASE_GLOBAL_API + 'v2/user/profile'
        self.TOKEN_URL = BASE_GLOBAL_API + 'token'
        self.GRAPHQL_URL = BASE_SEARCH_API + 'svc/search/v2/graphql'

        self.API_KEY = '2I84ZDjA2raVJ3hyTdADwdwxgDz7r62J8J0W8bE8N8VVILY446gDlrEB33fqLaXD'

        self.LANGUAGE = 'en'
        self.COUNTRY = 'UK'
        self.ACCESS_TOKEN = ''
        self.REFRESH_TOKEN = ''

        self.HEADERS = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'authorization': self.ACCESS_TOKEN
        }

        self.DATA = {
            'query': '',
            'operationName': '',
            'variables': {}
        }

    def _search_query(self):
        recv = requests.post(self.GRAPHQL_URL, headers=self.HEADERS, json=self.DATA).json()
        if 'errors' in recv:
            err = recv['errors'][0]
            loc = err['locations'][0] if 'locations' in err else None
            raise Client.SearchError(err['message'], loc)
        return recv

    def channels(self):
        self.DATA['query'] = '{ onNow: query(index: "eurosport_global_on_now", type: "Airing", page_size: 500) @context(uiLang: "%s") { hits { hit { ... on Airing { type liveBroadcast linear runTime startDate endDate expires genres playbackUrls { href rel templated } channel { callsign } photos { uri width height } mediaConfig { state productType type } titles { language title descriptionLong } } } } } }' % (self.LANGUAGE)
        recv = self._search_query()
        ret = []
        for hit in recv.get('data', {}).get('onNow', {}).get('hits', []):
            ret.append(Channel(hit['hit'], self))
        return ret

    def categories(self):
        self.DATA['query'] = '{ ListByTitle(title: "sports_filter") { list { ... on Category { id: sport sport tags { type displayName } defaultAssetImage { rawImage width height photos { imageLocation width height } } } } } } '
        recv = self._search_query()
        return recv.get('data', {}).get('ListByTitle', {}).get('list', [])

    def videos(self, id):
        self.DATA['query'] = '{ sport_%s:query (index: "eurosport_global",sort: new,page: 1,page_size: 100,type: ["Video","Airing"],must: {termsFilters: [{attributeName: "category", values: ["%s"]}]},must_not: {termsFilters: [{attributeName: "mediaConfigState", values: ["OFF"]}]},should: {termsFilters: [{attributeName: "mediaConfigProductType", values: ["VOD"]},{attributeName: "type", values: ["Video"]}]}) @context(uiLang: "%s") { ... on QueryResponse { ...queryResponse }} }fragment queryResponse on QueryResponse {meta { hits }hits {hit { ... on Airing { ... airingData } ... on Video { ... videoData } }}}fragment airingData on Airing {type contentId mediaId liveBroadcast linear partnerProgramId programId runTime startDate endDate expires genres playbackUrls { href rel templated } channel { id parent callsign partnerId } photos { id uri width height } mediaConfig { state productType type } titles { language title descriptionLong descriptionShort episodeName } }fragment videoData on Video {type contentId epgPartnerProgramId programId appears releaseDate expires runTime genres media { playbackUrls { href rel templated } } titles { title titleBrief episodeName summaryLong summaryShort tags { type value displayName } } photos { rawImage width height photos { imageLocation width height } } }' % (id, id, self.LANGUAGE)
        recv = self._search_query()
        return recv

    def epg(self, prev_date, date):
        self.DATA['query'] = '{ Airings: query(index: "eurosport_global_all", type: "Airing", from: "%sT22:00:00.000Z", to: "%sT21:59:59.999Z", sort: new, page_size: 500) @context(uiLang: "%s") { hits { hit { ... on Airing {type contentId mediaId liveBroadcast linear partnerProgramId programId runTime startDate endDate expires genres playbackUrls { href rel templated } channel { id parent callsign partnerId } photos { id uri width height } mediaConfig { state productType type } titles { language title descriptionLong descriptionShort episodeName } } } } } }' % (prev_date, date, self.LANGUAGE)
        return requests.post(self.GRAPHQL_URL, headers=self.HEADERS, json=self.DATA).json()

    def streams(self, url):
        headers = {
            'accept': 'application/vnd.media-service+json; version=1',
            'authorization': self.ACCESS_TOKEN
        }
        json_data = requests.get(url.format(scenario='browser~unlimited'), headers=headers).json()
        json_data['token'] = self.ACCESS_TOKEN
        return json_data

    def authorization(self, grant_type='refresh_token', token=''):
        #if token == '':
         #   token = addon.getSetting('device_id')
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'authorization': 'Bearer ' + self.API_KEY
        }
        data = {
            'grant_type': grant_type,
            'platform': 'browser',
            'token': token
        }
        return requests.post(self.TOKEN_URL, headers=headers, data=data).json()

    def authentication(self, credentials):
        headers = {
            'accept': 'application/vnd.identity-service+json; version=1.0',
            'content-type': 'application/json',
            'authorization': self.authorization(grant_type='client_credentials')['access_token']
        }
        data = {
            "type": "email-password",
            "email": {
                "address": credentials.email
            },
            "password": {
                "value": credentials.password
            }
        }
        return requests.post(self.IDENTITY_URL, headers=headers, json=data).json()

    def user(self):
        headers = {
            'accept': 'application/vnd.identity-service+json; version=1.0',
            'content-type': 'application/json',
            'authorization': self.ACCESS_TOKEN
        }
        return requests.get(self.USER_URL, headers=headers).json()

    def user_settings(self, data):
        print('token refreshed')
        self.ACCESS_TOKEN = data['access_token']
        self.REFRESH_TOKEN = data['refresh_token']
        self.HEADERS['authorization'] = self.ACCESS_TOKEN
        #addon.setSetting('access_token', self.ACCESS_TOKEN)
        #addon.setSetting('refresh_token', self.REFRESH_TOKEN)

    def profile(self):
        json_data = self.user()
        if json_data.get('message', ''):
            log('[{0}] {1}'.format(addon_id, utfenc(json_data['message'][:100])))
            self.user_settings(self.authorization(token=self.REFRESH_TOKEN))
            json_data = self.user()
        properties = json_data['profile']['profileProperty']
        for i in properties:
            name = i['name']
            if name == 'country':
                self.COUNTRY = i['value']
                #addon.setSetting('country', self.COUNTRY)
            if name == 'language':
                self.LANGUAGE = i['value']
                #addon.setSetting('language', self.LANGUAGE)
        print('country: %s language: %s' % (self.COUNTRY, self.LANGUAGE))

    def login(self):
        code = None
        json_data = self.authentication(self.credentials)
        if json_data.get('message'):
            print('%s' % utfenc(json_data['message'][:100]))
        else:
            print('logged in')
            code = json_data['code']
        if code:
            self.user_settings(self.authorization(grant_type='urn:mlbam:params:oauth:grant_type:token', token=code))
            self.profile()

