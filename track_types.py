# Todo: implement an "add self to own service playlist" function on each TrackType
# Todo: TrackTypes should hold a copy (reference technically) of their relevant service to perform these kinds of
# actions with

from services import GetSpotifyService
from spotipy import SpotifyException
from re import sub as regex_substitute


class TrackNotFoundException(Exception):
    """
    Raise to indicate failure to find a relevant track in the service self-search
    """


class Track:
    """
    Parent class from which to inherit the base fields required for the functionality provided by the bot
    Intended to be extended by the individual service type implementations.
    """

    def __init__(self, track_id, title, username, service, playlist):
        self.id = track_id
        self.title = title
        self.added_by = username
        self.link = ''
        self.service = service
        self.service_name = ''
        self.playlist_id = playlist

    def get_own_current_playlist(self):
        raise NotImplementedError

    def search_own_service_for_track_title(self):
        raise NotImplementedError

    def add_self_to_own_service(self):
        raise NotImplementedError

    def add_self_to_own_playlist(self):
        """
        Generic method utilising the other overridden methods for an instance of this class to add itself to its own 
        service's playlist.
        :return: True / False, indicating whether the track has been successfully added to the playlist, or whether it 
        has was already present and therefore did not need to be added.
        """
        if self.id is None:
            if not self.search_own_service_for_track_title():
                raise TrackNotFoundException
        playlist = self.get_own_current_playlist()
        if self.id not in playlist:
            self.add_self_to_own_service()
            return True
        else:
            return False


class YoutubeVideo(Track):
    """
    Class designed to hold the pertinent details relating to a YouTube video (either one that has been read in from user
    submission or parsed from a search result
    """

    def __init__(self, video_id, video_title, username, service, playlist='DEFAULT'):
        # TODO: Make playlist IDs gettable from a config file / create a playlist with a set name if doesn't exist to
        # add to ad infinitum
        super().__init__(video_id, video_title, username, service, playlist)
        if video_id is not None:
            self.format_link()
        self.service_name = 'YouTube'

    def format_link(self):
        self.link = 'https://www.youtube.com/watch?v={}'.format(self.id)

    def get_own_current_playlist(self):
        """
        Retrieves list of all videos currently present in the Youtube playlist. Used to prevent attempting to add 
        duplicates.
        :return: List of all of the unique IDs of the videos currently in the playlist
        """
        video_request = self.service.playlistItems().list(
            part="snippet", playlistId=self.playlist_id, maxResults=50
        )

        video_list = []

        while video_request:
            video_query_return = video_request.execute()
            video_response = video_query_return['items']
            for video in video_response:
                video_list.append(video['snippet']['resourceId']['videoId'])
                pass

            video_request = self.service.playlistItems().list_next(
                video_request, video_query_return
            )
        return video_list

    @property
    def search_own_service_for_track_title(self):
        """
        Performs a search of the YouTube service based on the track information held in the local variables
        :return: True if a track has been successfully found, otherwise False
        """

        search_term = self.title

        search_response = self.service.search().list(
            q=search_term,
            part='id,snippet',
            maxResults=10
        ).execute()

        for search_result in search_response.get('items', []):
            if search_result['id']['kind'] == 'youtube#video':
                self.id = search_result['id']['videoId']
                self.title = search_result['snippet']['title']
                self.format_link()
                return True

        return False

    def add_self_to_own_service(self):
        """
        Barebones call to the YouTube API to add the currently held track to the playlist.
        The assumption is made that any checks should have been performed before now in terms of the correctness of the 
        held data
        """

        add_action_body = \
        {
            'snippet':
            {
                'playlistId': self.playlist_id,
                'resourceId':
                {
                    'kind': 'youtube#video',
                    'videoId': self.id
                }
            }
        }

        self.service.playlistItems().insert(part='snippet', body=add_action_body).execute()


class SpotifyTrack(Track):
    """
    Class designed to hold the pertinent details relating to a Spotify track (either one that has been read in from user
    submission or parsed from a search result
    """

    @staticmethod
    def format_spotify_search_string(search_string):
        """
        Strip out anything between square brackets, as it's usually shite.
        Clear out any sets of parentheses which have certain keywords in to avoid fouling the Spotify search
        (But not clear everything in brackets, due to some tracks featuring other artists etc)
        :return: Search string formatted to be suitable to provide to a Spotify track search
        """
        search_string = search_string.lower()
        search_string = regex_substitute(r' *\[[^)]*\] *', '', search_string)
        search_string = regex_substitute(r'\(.*official.*\)', '', search_string)
        search_string = regex_substitute(r'\(.*lyric.*\)', '', search_string)
        search_string = regex_substitute(r'\(.*new.*\)', '', search_string)
        return search_string

    def search_own_service_for_track_title(self):
        """
        Performs cross-searching of Spotify when the user has supplied a Youtube link
        :return: True / False for success / failure of finding a relevant item in the cross - search
        """
        search_string = self.format_spotify_search_string(self.title)
        search_response = None
        attempt_successful = False

        while not attempt_successful:
            try:
                search_response = self.service.search(search_string, limit=1, type='track')
                attempt_successful = True
            except SpotifyException:
                self.service = GetSpotifyService()

        if 'tracks' in search_response:
            if len(search_response['tracks']['items']) > 0:
                found_track = search_response['tracks']['items'][0]
                self.id = found_track['id']
                self.title = '{} {} {}'.format(found_track['artists'][0]['name'], '-', found_track['name'])
                return True

        return False

    def format_link(self):
        self.link = 'https://open.spotify.com/track/{}'.format(self.id)

    def get_full_track_info(self):
        track_info = None
        attempt_successful = False
        while not attempt_successful:
            try:
                track_info = self.service.track(self.id)
                attempt_successful = True
            except SpotifyException:
                self.service = GetSpotifyService()
        print(track_info)

    def __init__(self, track_id, track_title, username, service, playlist='DEFAULT'):
        super().__init__(track_id, track_title, username, service, playlist)
        if track_id is not None:
            self.format_link()
            self.get_full_track_info()
        self.service_name = 'Spotify'

    def get_own_current_playlist(self):
        """
        Retrieves list of all tracks currently present in the Spotify playlist. Used to prevent attempting to add 
        duplicates.
        :return: List of unique track IDs currently present in the playlist
        """
        track_list = []
        attempt_successful = False
        while not attempt_successful:
            try:
                playlist_tracks = \
                self.service.user_playlist('strongohench', self.playlist_id, fields='tracks, next')[
                    'tracks']
                tracks = playlist_tracks['items']
                for track in tracks:
                    track_list.append(track['track']['id'])
                    pass
                while playlist_tracks['next']:
                    playlist_tracks = self.service.next(playlist_tracks)
                    tracks = playlist_tracks['items']
                    for track in tracks:
                        track_list.append(track['track']['id'])
                        pass
                attempt_successful = True
            except SpotifyException:
                self.service = GetSpotifyService()
        return track_list

    def add_self_to_own_service(self):
        """
        Adds the supplied track to the playlist (if not already present).
        """
        self.service.user_playlist_add_tracks('strongohench', self.playlist_id, [self.id])


class GooglePlayTrack(Track):
    """
    Class designed to hold the pertinent details relating to a Google Play Music track (either one that has been read 
    in from user submission or parsed from a search result
    """
    # TODO: Implement the full range of functionality for Google Play in line with the others
    def __init__(self, track_id, track_title, username, service, playlist='DEFAULT'):
        super().__init__(track_id, track_title, username, service, playlist)
        self.link = 'https://play.google.com/music/m/{}'.format(self.id)
        self.service_name = 'play.google.com'