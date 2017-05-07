from os import path
import sys
import httplib2
from argparse import ArgumentParser

from googleapiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow
from music_bot import MusicBot

CHANGELOG_DIR = 'changelogs/'

YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
DEFAULT_CLIENT_SECRETS_LOCATION = ""
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   {filepath}

with information from the Developers Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""".format(filepath=path.abspath(path.join(path.dirname(__file__),
                                           DEFAULT_CLIENT_SECRETS_LOCATION)))


def get_authenticated_service(client_secrets):
    """
    Used to create an authenticated Youtube service for subsequent use, passed in to the Bot's constructor to be kept 
    as a member variable. For an unknown reason the authentication process fails when placed in the helpers.py file, or 
    this would be treated in the same way as the Spotify service creation.
    """
    flow = flow_from_clientsecrets(client_secrets, scope=YOUTUBE_READ_WRITE_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)
    filename = (sys.argv[0].split('/'))[-1]
    storage = Storage(path.abspath(path.join(path.dirname(__file__),
                                             "client_secrets\{}-oauth2.json".format(filename))))
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage)

    sys.modules['win32file'] = None

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http=credentials.authorize(httplib2.Http()))


if __name__ == '__main__':

    parser = ArgumentParser(
        description='Slack MusicBot to automatically aggregate playlists based on user-submitted tracks')

    parser.add_argument('-cs', '--client_secrets', help='"Client Secrets" filepath containing YouTube auth information',
                        required=True)
    parser.add_argument('-s', '--slack_token', help='Slack Auth Token', required=True)
    parser.add_argument('-sa', '--spotify_auth', help='Spotify authentication information filepath', required=True)

    args = parser.parse_args()

    client_secrets_file = args.client_secrets
    spotify_auth_path = args.spotify_auth
    slack_token = args.slack_token

    carry_on = True

    while carry_on:
        try:
            slack = MusicBot(slack_token, get_authenticated_service(client_secrets_file), spotify_auth_path)
            slack.start()
        except ConnectionResetError:
            print('Thing dun broke. Trying it again.')
