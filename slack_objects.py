from event_logger import Logger


# Object to hold the individual attachments in a message
class SlackAttachment:
    """Secondary member class to hold the details of an attachment received in a message from an event"""

    def __init__(self, attachment_json):
        self.service_name = attachment_json['service_name']
        self.title = attachment_json['title']
        self.from_url = attachment_json['from_url']
        # self.service_icon = attachment_json['service_icon']
        self.id = None
        if self.service_name == 'YouTube':
            temp_id = ''
            if '.be/' in self.from_url:
                temp_id = self.from_url.split('.be/')[1]
                pass
            elif 'watch' in self.from_url:
                temp_id = self.from_url.split('?v=')[1]
                pass
            self.id = temp_id.split('&')[0]
            pass
        elif self.service_name == 'Spotify' and 'track' in self.from_url:
            if '?' in self.from_url:
                self.from_url = self.from_url.split('?')[0]
            if self.from_url.count(':') > 1:
                self.id = self.from_url.split(':')[-1]
            else:
                self.id = self.from_url.split('track/')[1]
        pass


class SlackMessage:
    """Member class to hold the details of a message received from an event"""

    # Check the type of each attachment in a message and create relevant objects for each
    @staticmethod
    def parse_attachments(attachment_list):
        """
        X-many attachments can be received in a message, so this parses all present in the JSON, forms an object for 
        each, and aggregates them in a list 
        """
        temp_attachments = []
        for attachment in attachment_list:
            if 'service_name' in attachment:
                if attachment['service_name'] == 'YouTube' or attachment['service_name'] == 'Spotify':
                    temp_attachments.append(SlackAttachment(attachment))
                else:
                    Logger.unrecognised_service(attachment['service_name'])

        return temp_attachments

    def __init__(self, message_json):
        if 'thread_ts' in message_json:
            self.is_reply = True
        else:
            self.is_reply = False
        if 'user' in message_json:
            self.user = message_json['user']
        else:
            self.user = None
        self.text = message_json['text']
        self.timestamp = message_json['ts']
        self.attachments = None
        if 'attachments' in message_json:
            self.attachments = self.parse_attachments(message_json['attachments'])
        pass


# Object to hold the actual event that has come in
class SlackEvent:
    """Encapsulating class to hold the pertinent data from an incoming event in order to facilitate easier access"""

    # Object to hold the message data within the event

    def __init__(self, event_json):
        self.channel = None
        if 'channel' in event_json:
            self.channel = event_json['channel']
        self.type = None
        if 'type' in event_json:
            self.type = event_json['type']
        self.message = None
        if 'message' in event_json:
            self.message = SlackMessage(event_json['message'])
            pass
