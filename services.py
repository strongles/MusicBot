#TODO: Have wrapper classes here for YouTube, Spotify and Play api services toegther with add to self methods
from auth_data import SpotifyAuthData
from spotipy import util, Spotify

def GetSpotifyService(auth_path=r'C:\Users\willro\PycharmProjects\MusicBot\client_secrets\spotify_auth_data.json'):
    """
    This is going to be a bit of a nasty workaround for the time being
    TODO: Make this not gross
    :param auth_path: Path to Spotify authentication data
    :return: Authenticated Spotify service for use in
    """

    spotify_auth_data = SpotifyAuthData(auth_path)

    token = util.prompt_for_user_token(spotify_auth_data.username,
                                       spotify_auth_data.scope,
                                       client_id=spotify_auth_data.client_id,
                                       client_secret=spotify_auth_data.client_secret,
                                       redirect_uri=spotify_auth_data.redirect_uri)

    service = Spotify(auth=token)

    return service