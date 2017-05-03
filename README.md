# MusicBot
Slackbot written in Python to aggregate music links to common playlists using the YouTube and Spotify APIs

Called from the command line, the main script expects three argument:
  -s    Slack API token
  -cs   Filepath to a YouTube Client Secrets JSON file (as provided when acquired from the Developer Dashboard here https://console.developers.google.com/)
  -sa   Filepath to a JSON file containing Spotify OAuth information (in the format shown in the template file present)
