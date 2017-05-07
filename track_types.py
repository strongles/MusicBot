class Track:
    """
    Parent class from which to inherit the base fields required for the functionality provided by the bot
    Intended to be extended by the individual service type implementations.
    """

    def __init__(self, track_id, title, username):
        self.id = track_id
        self.title = title
        self.added_by = username
        self.link = ''


class YoutubeVideo(Track):
    """
    Class designed to hold the pertinent details relating to a YouTube video (either one that has been read in from user
    submission or parsed from a search result
    """

    def __init__(self, video_id, video_title, username):
        super().__init__(video_id, video_title, username)
        self.link = 'https://www.youtube.com/watch?v={}'.format(self.id)


class SpotifyTrack(Track):
    """
    Class designed to hold the pertinent details relating to a Spotify track (either one that has been read in from user
    submission or parsed from a search result
    """

    def __init__(self, track_id, track_title, username):
        super().__init__(track_id, track_title, username)
        self.link = 'https://open.spotify.com/track/{}'.format(self.id)
