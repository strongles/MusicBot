from os import path
import sys
import httplib2
import argparse

from googleapiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow
from helpers import Bot

parser = argparse.ArgumentParser(description='Slack MusicBot to automatically aggregate playlists based on user-submitted tracks')
parser.add_argument('-cs','--client_secrets', help='"Client Secrets" filepath containing YouTube auth information', required=True)
parser.add_argument('-s','--slack_token', help='Slack Auth Token', required=True)
parser.add_argument('-sa', '--spotify_auth', help='Spotify authentication information filepath', required=True)
args = parser.parse_args()

CLIENT_SECRETS_FILE = args.client_secrets
SPOTIFY_AUTH_PATH = args.spotify_auth
SLACK_TOKEN = args.slack_token

CHANGELOG_DIR = 'changelogs/'

YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
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
                                   CLIENT_SECRETS_FILE)))


def get_authenticated_service():
    """Used to create an authenticated Youtube service for subsequent use, passed in to the Bot's constructor to be kept as a member variable.
        For an unknown reason the authentication process fails when placed in the helpers.py file, or this would be treated in the same way as the
        Spotify service creation."""
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_READ_WRITE_SCOPE, message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("{filename}-oauth2.json".format(filename=sys.argv[0]))
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage)

    sys.modules['win32file'] = None

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http=credentials.authorize(httplib2.Http()))

carry_on = True
while carry_on:
    try:
        slack = Bot(SLACK_TOKEN, get_authenticated_service(), SPOTIFY_AUTH_PATH)
        slack.start()
    except ConnectionResetError:
        print('Thing dun broke. Trying it again.')
