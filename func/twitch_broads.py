
import requests


class TwitchBroad:
    __TWITCH_ACCESS_TOKEN = None
    __CLIENT_ID = None
    __CLIENT_SECRET = None
    headers = None

    twitch_oauth_token_url = 'https://id.twitch.tv/oauth2/token'
    twitch_stream_url = "https://api.twitch.tv/helix/streams"
    PARAM_LENGTH_LIMIT = 100

    @staticmethod
    def make_list_in_list(lst, length_limit):
        return [lst[i * length_limit: (i + 1) * length_limit]
                for i in range((len(lst) + length_limit - 1) // length_limit)]

    def __init__(self, client_id, client_secret):
        self.__CLIENT_ID = client_id
        self.__CLIENT_SECRET = client_secret
        # self.__getOauthToken(client_id, client_secret)

    # Authenticate with Twitch, get Oauth token and set "headers" member
    def __getOauthToken(self):
        res = requests.post(self.twitch_oauth_token_url, data={
            'client_id': self.__CLIENT_ID,
            'client_secret': self.__CLIENT_SECRET,
            'grant_type': 'client_credentials'
        })
        if res:
            data = res.json()
            self.__TWITCH_ACCESS_TOKEN = data['access_token']
            self.headers = {
                'Client-ID': self.__CLIENT_ID,
                'Authorization': 'Bearer %s' % (self.__TWITCH_ACCESS_TOKEN)
            }
        else:
            print('Error occurred while getting oauth token from %s' %
                  self.twitch_oauth_token_url)

    def get_broads(self, streamers):
        try:
            self.__getOauthToken()
        except:
            return []

        streamers_data = list()  # stream data list

        if len(streamers) > self.PARAM_LENGTH_LIMIT:
            list_in_list = make_list_in_list(
                streamers, self.PARAM_LENGTH_LIMIT)

            for request_streamers in list_in_list:
                params = {
                    'language': 'ko',
                    'user_id': request_streamers,
                    'game_id': '21779'
                }

                # request to the Twitch Api
                res = requests.get(
                    self.twitch_stream_url,
                    headers=self.headers,
                    params=params)

                if res:
                    data = res.json()
                    streamers_data.extend(data['data'])
        else:
            params = {
                'language': 'ko', 'user_id': streamers
            }

            # Request to the Twitch Api
            res = requests.get(
                self.twitch_stream_url,
                headers=self.headers,
                params=params)

            if res:
                data = res.json()
                streamers_data.extend(data['data'])

        return [('twitch', stream['user_login'], stream['id']) for stream in streamers_data]