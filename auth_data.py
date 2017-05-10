from json import load as json_load
from os import path


class SpotifyAuthData:
    """
    Holds the information necessary to create an authenticated Spotify service object
    """

    def __init__(self, filepath):
        if not path.isfile(filepath):
            print("Spotify auth data file does not exist.")
            raise FileNotFoundError

        with open(filepath, 'r') as file_in:
            data = json_load(file_in)

        self.username = data['username']
        self.scope = data['scope']
        self.client_secret = data['client_secret']
        self.client_id = data['client_id']
        self.redirect_uri = data['redirect_uri']


class PlayLoginData:
    """
    Local object holding login information for Google Play Music, read from a json file
    """

    def __init__(self, filepath):
        if not path.isfile(filepath):
            print("Google Play Music login information not found at path: {}"
                  .format(filepath))
            raise FileNotFoundError

        with open(filepath, 'r') as file_in:
            data = json_load(file_in)

        self.username = data['username']
        self.password = data['password']