from json import dumps as json_dumpstring
import time


class Logger:
    """
    Utility class used to handle server-side logging in the event of certain actions
    """

    def __init__(self):
        pass

    @staticmethod
    def song_added(song, playlist_id):
        """
        Prints server logging on success of addition of song to playlist.
        """
        if song.added_by == 'cedmunds90':
            print('Ruhpushuh {song_id} ({title}) ruhpush a shuh {playlist_id} rhup {added_by}.'
                  .format(song_id=song.id,
                          title=song.title,
                          playlist_id=playlist_id,
                          added_by=song.added_by))
            pass
        else:
            print('Song {song_id} ({title}) added to playlist {playlist_id} by {added_by}.'
                  .format(song_id=song.id,
                          title=song.title,
                          playlist_id=playlist_id,
                          added_by=song.added_by))

            pass

    @staticmethod
    def song_already_exists(song, playlist_id):
        """
        Prints server logging on attempted song addition when song already exists in playlist.
        """
        print('Song {title} already in playlist {playlist_id}, adding has been skipped.'
              .format(title=song,
                      playlist_id=playlist_id))
        pass

    @staticmethod
    def unrecognised_format(link):
        """
        Server logging for receipt of unsupported YouTube link format.
        """
        print('Message has been identified as a YouTube link, but the format is not recognised.')
        print('Message was {}, support for this format should be added soon.'.format(link))
        pass

    @staticmethod
    def unrecognised_service(service_name):
        """
        Server logging for reciept of unsupported service/attachment type.
        """
        print('Service {} not (yet) supported.'.format(service_name))
        pass

    @staticmethod
    def future_supported_service(service_name):
        """
        Server logging for receipt of service for which support is planned for a future version.
        """
        print('Service {} linked.'.format(service_name))
        pass

    @staticmethod
    def failed_to_find_relevant_youtube_video(track_name):
        """
        Server logging when Spotify->YouTube cross-search fails to return a video to add to the playlist.
        """
        print('YouTube Service search for {} did not bring back an appropriate video.'.format(track_name))
        pass

    @staticmethod
    def failed_to_find_relevant_spotify_track(video_title):
        """
        Server logging when YouTube->Spotify cross-search fails to return a track to add to the playlist.
        """
        print('Spotify Service search for {} did not bring back an appropriate track.'.format(video_title))
        pass

    @staticmethod
    def log_event_to_file(event):
        """
        Logging of received event JSON to file.
        """
        with open('eventlogs/{}.json'.format(time.time()), 'w') as event_write:
            event_write.write(json_dumpstring(event))
        pass

    @staticmethod
    def playlist_contents_requested(service_name):
        """
        Server logging when a request for the contents of a playlist is requested
        """
        print('Request for contents of {} playlist received.'.format(service_name))
        pass
