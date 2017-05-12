# Todo: implement an "add self to own service playlist" function on each TrackType
# Todo: TrackTypes should hold a copy (reference technically) of their relevant service to perform these kinds of actions with

from services import GetSpotifyService
from spotipy import SpotifyException

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


    def add_self_to_own_service(self):
        raise NotImplementedError

    def get_own_current_playlist(self):
        raise NotImplementedError



class YoutubeVideo(Track):
    """
    Class designed to hold the pertinent details relating to a YouTube video (either one that has been read in from user
    submission or parsed from a search result
    """

    def __init__(self, video_id, video_title, username, service, playlist='DEFAULT'):
        # TODO: Make playlist IDs gettable from a config file / create a playlist with a set name if doesn't exist to add to ad infinitum
        super().__init__(video_id, video_title, username, service, playlist)
        self.link = 'https://www.youtube.com/watch?v={}'.format(self.id)
        self.service_name = 'YouTube'

    def get_own_current_playlist(self):
        return self.videos_in_playlist(self.playlist_id)

    def videos_in_playlist(self, playlist):
        """
        Retrieves list of all videos currently present in the Youtube playlist. Used to prevent attempting to add 
        duplicates.
        """
        video_request = self.service.playlistItems().list(
            part="snippet", playlistId=playlist, maxResults=50
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


    def add_self_to_own_service(self):
        """
        Adds the supplied video to the playlist (if not already present).
        Return is success or failure of addition
        This build assumes an unsuccessful addition is indicative of the track already existing in the playlist
        """
        existing_videos = self.get_own_current_playlist()
        if self.id not in existing_videos:
            self.service.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': self.playlist_id,
                        'resourceId': {
                            'kind': 'youtube#video',
                            'videoId': self.id
                        }
                    }
                }
            ).execute()
            return True
            #self.logger.song_added(video, playlist)
            #self.mark_message_as_added_to_playlist(event.channel, event.message.timestamp, 'yt')
        else:
            return False
            #self.mark_song_as_already_existing(event.channel, event.message.timestamp, 'yt')
            #self.logger.song_already_exists(video, playlist)


class SpotifyTrack(Track):
    """
    Class designed to hold the pertinent details relating to a Spotify track (either one that has been read in from user
    submission or parsed from a search result
    """

    def __init__(self, track_id, track_title, username, service, playlist='DEFAULT'):
        super().__init__(track_id, track_title, username, service, playlist)
        self.link = 'https://open.spotify.com/track/{}'.format(self.id)
        self.service_name = 'Spotify'

    def get_own_current_playlist(self):
        return self.tracks_in_playlist(self.playlist_id)

    def tracks_in_playlist(self, playlist):
        """
        Retrieves list of all tracks currently present in the Spotify playlist. Used to prevent attempting to add 
        duplicates.
        """
        track_list = []
        attempt_successful = False
        while not attempt_successful:
            try:
                playlist_tracks = \
                self.service.user_playlist('strongohench', playlist, fields='tracks, next')[
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

    def add_self_to_own_service(self):#, track, event, playlist='3RBeSdvsH57tbsqNZHS44A'):
        """
        Adds the supplied track to the playlist (if not already present).
        """
        attempt_successful = False
        existing_tracks = []
        while not attempt_successful:
            try:
                existing_tracks = self.tracks_in_playlist(self.playlist_id)
                attempt_successful = True
            except SpotifyException:
                self.service = GetSpotifyService()
        if self.id not in existing_tracks:
            self.service.user_playlist_add_tracks('strongohench', self.playlist_id, [self.id])
            return True
            #self.logger.song_added(track, playlist)
            #self.mark_message_as_added_to_playlist(event.channel, event.message.timestamp, 'spot')
        else:
            return False
            #self.mark_song_as_already_existing(event.channel, event.message.timestamp, 'spot')
            #self.logger.song_already_exists(track, playlist)


class GooglePlayTrack(Track):
    """
    Class designed to hold the pertinent details relating to a Google Play Music track (either one that has been read 
    in from user submission or parsed from a search result
    """

    def __init__(self, track_id, track_title, username, playlist='DEFAULT'):
        super().__init__(track_id, track_title, username, playlist)
        self.link = 'https://play.google.com/music/m/{}'.format(self.id)
        self.service_name = 'play.google.com'