# TikTok Discord Bot

Automatically replaces TikTok links with their embedded content (e.g. videos, images)

## Tools Used

- [Discord.py](https://discordpy.readthedocs.io/en/stable/) - A python wrapper for the Discord API
- [FFMPEG](https://ffmpeg.org/) - A complete, cross-platform solution to record, convert and stream audio and video
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - A youtube-dl fork with additional features and fixes
- [Docker](https://www.docker.com/) - A set of platform as a service products that use OS-level virtualization to deliver software in packages called containers

## Usage

- Make a Discord Bot
  - [Discord Developer Portal](https://discord.com/developers/applications)
- Add `TOKEN` (Discord Bot Token) to `.env`
- Build the docker image
  - `docker build -t tiktok-bot .`
- Run the docker image
  - `docker run -d --name tiktok-bot tiktok-bot`
- Send a TikTok link in a Discord channel that the bot has access to
- The bot is now running and will automatically replace the link with the embedded content

## Limiations

- Discord does not permit bots to send files [>25MB](https://www.pcgamer.com/discords-upping-its-puny-file-upload-size-limit-for-all-users/), so videos larger than this will not be sent
- The bot does not handle edits to messages, so if a message is edited to a TikTok link, the bot will not replace it
- The bot cannot retrieve TikTok videos that were deleted. Sometimes your phone or website will cache the video, so it may still be viewable, but the bot will not be able to retrieve it (and neither will you if you refresh the page)

## Customization

You can change the bot settings in `settings.py`
The bot settings are described below

- `prefix` - The prefix for bot commands
- `compression` - The compression level for the video (0 is lossless, 51 is worst quality)
- `default_rs_count` - The default number of messages to rescan when using the `-rs` command
- `emojis` - The emoji names
- `download_dir` - The folder where the videos and photos will be downloaded

## Commands

- `-rs <optional: num>` - Rescans the last `num` (default 25) messages in the channel (if the bot was offline when the link was sent)
- `-ns` - Functions as a flag telling bot to ignore any TikTok links in the message. May be used anywhere in the message
