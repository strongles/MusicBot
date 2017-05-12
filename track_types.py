# Todo: implement an "add self to own service playlist" function on each TrackType
# Todo: TrackTypes should hold a copy (reference technically) of their relevant service to perform these kinds of actions with

class Track:
    """
    Parent class from which to inherit the base fields required for the functionality provided by the bot
    Intended to be extended by the individual service type implementations.
    """

    def __init__(self, track_id, title, username, service):
        self.id = track_id
        self.title = title
        self.added_by = username
        self.link = ''
        self.service = service
        self.service_name = ''

    def add_self_to_own_service(self):
        raise NotImplementedError



class YoutubeVideo(Track):
    """
    Class designed to hold the pertinent details relating to a YouTube video (either one that has been read in from user
    submission or parsed from a search result
    """

    def __init__(self, video_id, video_title, username, service):
        super().__init__(video_id, video_title, username, service)
        self.link = 'https://www.youtube.com/watch?v={}'.format(self.id)
        self.service_name = 'YouTube'

    def add_self_to_own_service(self):
        """
        Adds the supplied video to the playlist (if not already present).
        """
        existing_videos = self.videos_in_playlist(playlist)
        if video.id not in existing_videos:
            self.youtube_service.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': playlist,
                        'resourceId': {
                            'kind': 'youtube#video',
                            'videoId': video.id
                        }
                    }
                }
            ).execute()
            self.logger.song_added(video, playlist)
            self.mark_message_as_added_to_playlist(event.channel, event.message.timestamp, 'yt')
        else:
            self.mark_song_as_already_existing(event.channel, event.message.timestamp, 'yt')
            self.logger.song_already_exists(video, playlist)


class SpotifyTrack(Track):
    """
    Class designed to hold the pertinent details relating to a Spotify track (either one that has been read in from user
    submission or parsed from a search result
    """

    def __init__(self, track_id, track_title, username):
        super().__init__(track_id, track_title, username)
        self.link = 'https://open.spotify.com/track/{}'.format(self.id)
        self.service_name = 'Spotify'

class GooglePlayTrack(Track):
    """
    Class designed to hold the pertinent details relating to a Google Play Music track (either one that has been read 
    in from user submission or parsed from a search result
    """

    def __init__(self, track_id, track_title, username):
        super().__init__(track_id, track_title, username)
        self.link = 'https://play.google.com/music/m/{}'.format(self.id)
        self.service_name = 'play.google.com'