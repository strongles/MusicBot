from slackclient import SlackClient
from auth_data import SpotifyAuthData, PlayLoginData
from helpers import run_once
from re import sub as regex_substitute
from track_types import SpotifyTrack, YoutubeVideo, GooglePlayTrack
from spotipy.client import SpotifyException
from slack_objects import SlackEvent
from os import listdir
from websocket import WebSocketConnectionClosedException
from spotipy import Spotify, util
from event_logger import Logger
from gmusicapi import MobileClient


class MusicBot:
    """
    The actual Bot itself, this class handles all of the computation and decision making involved in the MusicBot 
    functionality.
    """

    @run_once
    def add_existing_youtube_playlist_to_spotify(self, yt_playlist, spot_playlist):
        """
        Performs a Spotify cross-search and playlist add for each item currently in the YouTube playlist. Catch-up 
        functionality seeing as Spotify support was implemented later. Bit filthy and nasty, but excusable for a 
        single-use thing.
        """
        query_request = self.youtube_service.playlistItems().list(
            part="snippet", playlistId=yt_playlist, maxResults=50
        )
        query_response = query_request.execute()
        query_request = self.youtube_service.playlistItems().list_next(
            query_request, query_response
        )
        query_response = query_request.execute()
        videos = query_response['items']
        tracks_found = []
        for video in videos:
            search_string = regex_substitute(r'[[](\w|\s)*[]]', '', video['snippet']['title'])
            print(search_string)
            search_response = self.spotify_service.search(search_string, limit=1, type='track')
            if 'tracks' in search_response:
                if len(search_response['tracks']['items']) > 0:
                    found_track = search_response['tracks']['items'][0]
                    tracks_found.append(SpotifyTrack(found_track['id'],
                                                     found_track['artists'][0]['name'] + ' - ' + found_track['name'],
                                                     'existing YouTube playlist'))
        tracks_in_playlist = self.tracks_in_playlist(spot_playlist)
        for track in tracks_found:
            if track.id not in tracks_in_playlist:
                self.spotify_service.user_playlist_add_tracks('strongohench', spot_playlist, [track.id])
                self.logger.song_added(track, spot_playlist)

    def search_youtube_for_spotify_track(self, track):
        """
        Performs cross-searching of Youtube when the user has supplied a Spotify link
        """
        search_response = self.youtube_service.search().list(
            q=track.title,
            part='id,snippet',
            maxResults=10
        ).execute()

        for search_result in search_response.get('items', []):
            if search_result['id']['kind'] == 'youtube#video':
                return YoutubeVideo(search_result['id']['videoId'], search_result['snippet']['title'], track.added_by)
        self.logger.failed_to_find_relevant_youtube_video(track.title)
        return None

    def api_call(self, *args, **kwargs):
        """
        Wrapper function to allow for cleaner access to the Slack service's API methods
        """
        return self.slack_service.api_call(*args, **kwargs)

    def get_username(self, user_id):
        """
        Uses the Slack API to retrieve the username of a given user when provided with their Slack User ID
        """
        user_info = self.api_call('users.info', user=user_id)
        if user_info is not None:
            return user_info['user']['name']

    def add_reaction(self, channel, timestamp, reaction_name):
        """
        Uses the Slack API to add a reaction to a given message
        """
        self.api_call('reactions.add', name=reaction_name, timestamp=timestamp, channel=channel)
        pass

    def mark_message_as_added_to_playlist(self, channel, timestamp, service):
        """
        Adds a reaction to the message that contained the submitted content. Called upon success of the addition 
        functions.
        """
        self.add_reaction(channel, timestamp, service + '_added')
        pass

    def mark_song_as_already_existing(self, channel, timestamp, service):
        """
        Adds a reaction to the message that contained the submitted content. Called when the submitted song already 
        exists within the relevant playlist
        """
        self.add_reaction(channel, timestamp, service + '_exists')
        pass

    def mark_song_as_unable_to_be_found(self, channel, timestamp, service):
        """
        Adds a reaction to the message that contained the submitted content. Called when the song is unable to be found 
        in the cross-search functionality.
        """
        self.add_reaction(channel, timestamp, service + '_not_found')
        pass

    def post_message(self, message, channel=None):
        """
        Wrapper function to allow for clean access to the API to post a message to a channel. Defaults to the MusicClub 
        channel if no other is provided.
        """
        if channel is not None:
            self.api_call('chat.postMessage', as_user=True, channel=channel, text=message)
        else:
            self.api_call('chat.postMessage', as_user=True, channel=self.default_channel, text=message)

    def post_reply(self, message_text, channel, timestamp):
        self.api_call('chat.postMessage', as_user=True, channel=channel, thread_ts=timestamp, text=message_text)

    def post_cross_search_failure(self, service, title, channel):
        """
        Informs the user when a cross-search for the content submitted has been unsuccessful.
        """
        self.api_call('chat.postMessage', as_user=True, channel=channel,
                      text='Cross searching on ' + service + ' failed to find ' + title)
        pass

    def post_debug_message(self, message):
        """
        Posts the supplied text within the direct message channel. 
        Intended for use when prototyping new functionality and the standard post_message function would either spam 
        the usual channel or would give away surprise new functionality.
        """
        get_channel_response = self.api_call('im.open', user='U1452LVK4')
        channel_id = get_channel_response['channel']['id']
        self.api_call('chat.postMessage', as_user=True, channel=channel_id, text=message)

    def log_event(self, event):
        """
        Logs the received JSON event string to file."""
        self.logger.log_event_to_file(event)

    def scan_for_youtube_video(self, event):
        """
        Deprecated function based on the old string manipulation approach used to analyse an incoming event and 
        ascertain if it was of the correct type (Youtube link) and if so extract the relevant data to be dealt with.
        """
        if 'type' in event:
            if event['type'] == 'message' and 'message' in event and 'attachments' in event['message']:
                self.log_event(event)
                attachments = event['message']['attachments']
                for attachment in attachments:
                    if 'service_name' in attachment:
                        if attachment['service_name'] == 'YouTube':
                            id_string = ''
                            if 'youtube.com' in attachment['from_url']:
                                id_string = attachment['from_url'].split('watch?v=')[1]
                            elif 'youtu.be' in attachment['from_url']:
                                id_string = attachment['from_url'].split('.be/')[1]
                            else:
                                self.post_message(
                                    'Link recognised as YouTube, but the format provided is not currently supported.')
                                self.logger.unrecognised_format(attachment['from_url'])
                            if len(id_string.split('&')) > 1:
                                return id_string.split('&')[0]
                            else:
                                return id_string
                        elif attachment['service_name'] == 'Spotify':
                            self.post_message(
                                'Spotify not currently supported, but in development for a future version.')
                            self.logger.future_supported_service('Spotify')
                        else:
                            service_name = attachment['service_name']
                            self.post_message('Sorry, service ' + service_name + ' is not currently supported.')
                            self.logger.unrecognised_service(service_name)

    def print_spotify_tracklist(self, channel, playlist=None):
        """
        Prints the current content of the Spotify playlist to the channel provided as a code snippet
        """
        if playlist is None:
            playlist = self.spotify_playlist
            pass

        playlist_track_titles = []
        attempt_successful = False
        while not attempt_successful:
            try:
                playlist_tracks = self.spotify_service.user_playlist('strongohench', playlist, fields='tracks, next')[
                    'tracks']
                tracks = playlist_tracks['items']
                for track in tracks:
                    playlist_track_titles.append(track['track']['artists'][0]['name'] + ' - ' + track['track']['name'])
                    pass
                while playlist_tracks['next']:
                    playlist_tracks = self.spotify_service.next(playlist_tracks)
                    tracks = playlist_tracks['items']
                    for track in tracks:
                        playlist_track_titles.append(
                            track['track']['artists'][0]['name'] + ' - ' + track['track']['name'])
                        pass
                attempt_successful = True
            except SpotifyException:
                self.spotify_service = self.get_spotify_service(self.spotify_auth_data)

        print_string = ''
        for title in playlist_track_titles:
            print_string += str(title) + '\n'
            pass

        output_title = '| SPOTIFY PLAYLIST CONTENTS ({}) TRACKS |\n'.format(len(playlist_track_titles))
        top_bottom = '-' * (len(output_title) - 1) + '\n'

        print_string = top_bottom + output_title + top_bottom + print_string

        print_string = print_string[:-1]

        self.api_call('files.upload', content=print_string, filename='Spotify_Playlist', mode='snippet',
                      channels=channel)
        pass

    def print_youtube_tracklist(self, channel, playlist=None):
        """Prints the current content of the YouTube playlist to the channel provided as a code snippet"""
        if playlist is None:
            playlist = self.youtube_playlist
            pass

        playlist_query = self.youtube_service.playlistItems().list(
            part="snippet", playlistId=playlist, maxResults=50
        )

        playlist_video_titles = []

        while playlist_query:

            playlist_results = playlist_query.execute()
            playlist_results_list = playlist_results['items']

            for track in playlist_results_list:
                playlist_video_titles.append(track['snippet']['title'])
                pass

            playlist_query = self.youtube_service.playlistItems().list_next(
                playlist_query, playlist_results
            )

        print_string = ''
        for title in playlist_video_titles:
            print_string += str(title) + '\n'
            pass

        output_title = '| YOUTUBE PLAYLIST CONTENTS ({}) TRACKS |\n'.format(len(playlist_video_titles))
        top_bottom = '-' * (len(output_title) - 1) + '\n'

        print_string = top_bottom + output_title + top_bottom + print_string

        print_string = print_string[:-1]

        self.api_call('files.upload', content=print_string, filename='YouTube_Playlist', mode='snippet',
                      channels=channel)
        pass

    def scan_for_relevant_attachment(self, event_json):
        """
        Object-based approach used to analyse an incoming event and determine whether or not it contains content to be 
        added to our playlists, and extracting this information if found.
        """
        event = SlackEvent(event_json)
        if event.type is not None:
            if event.type == 'message' and event.message is not None:
                if event.message.attachments is not None and not event.message.is_reply:
                    self.log_event(event_json)
                    for attachment in event.message.attachments:
                        if attachment.service_name is not None:
                            if attachment.service_name in self.track_type_map and attachment.id is not None:
                                relevant_track_type = self.track_type_map[attachment.service_name]
                                return relevant_track_type(attachment.id,
                                                           attachment.title,
                                                           self.get_username(event.message.user),
                                                           self.service_map[relevant_track_type])
                            '''
                            elif attachment.service_name == 'Spotify' and attachment.id is not None:
                                return SpotifyTrack(attachment.id, attachment.title,
                                                    self.get_username(event.message.user))
                            '''



    '''
    def add_video_to_playlist(self, video, event, playlist='PLDQ8Lg2Wj2nGKAL_7nLp8ELghxJgxVdRM'):
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
    '''


    def print_newest_unprinted_changelog(self, path):
        """
        Prints the changelog for the most recent version to the channel to inform the user of all currently available 
        functionality.
        """
        log_list = listdir(path)
        if len(log_list):
            current_logfile = log_list[0]
            for log in log_list:
                if log > current_logfile:
                    current_logfile = log
            logfile_path = path + current_logfile
            with open(logfile_path) as changelog:
                changelog_contents = changelog.readlines()
            if changelog_contents[-1] != 'PRINTED':
                message_text = ''''''
                for line in changelog_contents:
                    message_text += line
                self.post_message('```' + message_text + '```')
                with open(logfile_path, 'a') as writing_file:
                    writing_file.write('\nPRINTED')

    def reply_with_cross_searched_link(self, event, track):
        self.post_reply(track.link, event.channel, event.message.timestamp)
        # self.api_call('chat.postMessage', thread_ts=event.message.timestamp, channel=event.channel, text=track.link)

    def treat_song(self, found_song, source_event):
        '''
        if isinstance(found_song, YoutubeVideo):
            self.add_video_to_playlist(found_song, source_event)
            attempt_successful = False
            track = None
            while not attempt_successful:
                try:
                    track = self.search_spotify_for_youtube_video(found_song)
                    attempt_successful = True
                except SpotifyException:
                    self.spotify_service = self.get_spotify_service(self.spotify_auth_data)
            if track is not None:
                self.add_track_to_playlist(track, source_event)
                self.reply_with_cross_searched_link(source_event, track)
            else:
                pass
                #self.mark_found_song_as_unable_to_be_found(source_event.channel,
                 #                                    source_event.message.timestamp, 'yt')
        elif isinstance(found_song, SpotifyTrack):
            self.add_track_to_playlist(found_song, source_event)
            video = self.search_youtube_for_spotify_track(found_song)
            if video is not None:
                self.add_video_to_playlist(video, source_event)
                self.reply_with_cross_searched_link(source_event, video)

            else:
                self.mark_song_as_unable_to_be_found(source_event.channel,
                                                     source_event.message.timestamp, 'spot')
        else:
            self.logger.unrecognised_service('Unknown')
        '''

        found_song.add_self_to_own_service()


    def start(self):
        """
        Main loop function to listen for events from whatever channels the Bot is a member of (includes private message 
        channels as well as group conversations).
        """
        # self.post_message('VERSION UPDATE')
        self.print_newest_unprinted_changelog(self.default_changelog_location)
        # self.add_existing_youtube_playlist_to_spotify(self.youtube_playlist, self.spotify_playlist)
        attempts = 0
        while True:
            try:
                if self.slack_service.rtm_connect():
                    attempts = 0
                    while True:
                        for event in self.slack_service.rtm_read():
                            slack_event = SlackEvent(event)
                            song = self.scan_for_relevant_attachment(event)
                            if song is not None:
                                self.treat_song(song, slack_event)

                            elif 'type' in event:
                                if event['type'] == 'message':

                                    if 'text' in event:
                                        message_text = event['text']
                                    message_channel = event['channel']
                                    if '--list' in message_text:
                                        if 'spotify' in str.lower(message_text):
                                            self.print_spotify_tracklist(message_channel)
                                            self.logger.playlist_contents_requested('spotify')
                                            pass
                                        if 'youtube' in str.lower(message_text):
                                            self.print_youtube_tracklist(message_channel)
                                            self.logger.playlist_contents_requested('youtube')
                                            pass
                                    elif '--request' in message_text and message_text.split('--request')[0] == '':
                                        with open('request_feature.txt', 'a') as file_out:
                                            file_out.write(self.get_username(event['user']) + ': ' + message_text[len(
                                                '--request '):] + '\n')
                                        self.post_message('Feature request logged. Ty bitch.', message_channel)
                                        pass

                else:
                    print('Unable to communicate through connection. Restarting will probably resolve this issue.')
            except WebSocketConnectionClosedException:
                if attempts < 5:
                    attempts += 1
                    print('Websocket closed, attempting reconnect number {} (No news is good news)'.format(attempts))
                else:
                    print('Retries exceeded. Bailing.')
                    break

    @staticmethod
    def get_spotify_service(spotify_auth_data):
        """
        Used at initialisation to create an authenticated Spotify service for subsequent use, kept as a member variable 
        on the bot itself.
        """

        token = util.prompt_for_user_token(spotify_auth_data.username,
                                           spotify_auth_data.scope,
                                           client_id=spotify_auth_data.client_id,
                                           client_secret=spotify_auth_data.client_secret,
                                           redirect_uri=spotify_auth_data.redirect_uri)

        service = Spotify(auth=token)

        return service

    @staticmethod
    def get_play_service(login_information):
        play_api = MobileClient()
        if play_api.login(login_information.username, login_information.password, MobileClient.FROM_MAC_ADDRESS)
            return play_api
        else:
            raise Exception('Unable to acquire Google Play Music servi')


    def __init__(self, token, youtube, spotify_auth_path, play_login_file):
        self.slack_service = SlackClient(token)
        self.youtube_service = youtube
        self.spotify_auth_data = SpotifyAuthData(spotify_auth_path)
        self.play_auth_data = PlayLoginData(play_login_file)
        self.spotify_service = self.get_spotify_service(self.spotify_auth_data)
        self.play_service = self.get_play_service(self.play_auth_data)
        self.default_channel = 'C1WV7ME66'
        self.default_changelog_location = 'changelogs/'
        self.logger = Logger()
        self.youtube_playlist = 'PLDQ8Lg2Wj2nGKAL_7nLp8ELghxJgxVdRM'
        self.spotify_playlist = '3RBeSdvsH57tbsqNZHS44A'
        self.track_type_map = {
            'Spotify': SpotifyTrack,
            'YouTube': YoutubeVideo,
            'play.google.com': GooglePlayTrack
        }
        self.service_map = {
            SpotifyTrack: self.spotify_service,
            YoutubeVideo: self.youtube_service,
            GooglePlayTrack: self.play_service
        }