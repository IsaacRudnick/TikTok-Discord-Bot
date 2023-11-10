from settings import *  # Import all settings from settings.py
import asyncio  # For the sleep function
import shutil  # For deleting directories with files in them
import re  # For finding the photo URLs in the TikTok HTML
import discord  # For the bot
import requests  # For downloading the TikTok HTML
from yt_dlp import YoutubeDL  # For downloading the TikTok video
from ffmpeg.asyncio import FFmpeg
import os  # For creating directories and deleting files
from dotenv import load_dotenv  # For loading the .env file
load_dotenv()  # Load the .env file

# Create a bot instance
intents = discord.Intents.all()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print("\n")  # Add a newline for readability
    print(f"Starting bot v{version}")
    # Make the downloads folder if it doesn't exist
    if not os.path.exists(download_dir):
        print(f"Creating {download_dir} folder")
        os.mkdir(download_dir)

    # For every subfolder in downloads, delete it
    # There shouldn't be any files here, just folders of files, so we can use shutil.rmtree
    for folder in os.listdir(download_dir):
        print(f"Deleting {folder} folder")
        shutil.rmtree(os.path.join(download_dir, folder))

    print(f"Logged in as {client.user.name}")


async def handle_photo_slideshow(message: discord.Message, parent_folder: str):
    """This method will send a message with a link to the photo slideshow. 
    It will then download the HTML of the TikTok link, find the photo URLs,
    download the photos, and send them a thread created from the message the bot sent.
    """
    link = message.content
    # Use bot's message as base of thread, so that the user is not pinged for every photo
    bot_message = await message.channel.send(
        f'*{message.author.name}*:\n<{link.split("?")[0]}>\n'
    )

    response = requests.get(link)

    strings = re.findall(r'"([^"]*)"', response.text)
    # Get rid of the strings that don't contain the word "i-photomode"
    strings = [s for s in strings if "i-photomode" in s]
    # Get rid of these strings, too, since they are invalid
    strings = [s for s in strings if "\\\\" not in s]
    strings = [s.replace("u002F", "").replace("\\", "/") for s in strings]

    names_and_urls = {}
    for string in strings:
        # Might be "i-photomode-tx" or "i-photomode-us" or something else
        start_index = string.find("i-photomode") + len("i-photomode-??")
        end_index = string.find("~")
        key = string[start_index + 1: end_index]
        names_and_urls[key] = string

    # To keep track of the photos
    filepaths = []
    for name, url in names_and_urls.items():
        name = name.replace("/", "-")
        response = requests.get(url)
        # Join the filepath with the downloads folder path
        filepath = f"{parent_folder}/{name}.jpeg"
        filepaths.append(filepath)
        with open(filepath, "wb") as f:
            f.write(response.content)

    # If the last character is a slash, remove it
    if link[-1] == "/":
        link = link[:-1]

    # Get the identifier in the link.
    # This makes the thread identifiable.
    # Examples:
    # "https://www.tiktok.com/@neverrcared/video/7221939078197955846/"
    # becomes "7221939078197955846"
    # Note that even though the URL says this is a video, it is actually a photo slideshow!
    # and "https://www.tiktok.com/t/ZTR3us331/"
    # becomes "ZTR3us331"
    thread_title = f"Slideshow Thread {link.split('/')[-1]}"
    thread = await bot_message.create_thread(name=thread_title)

    # Upload each photo to the thread.
    for filepath in filepaths:
        # Send the photo with the count and total number of photos
        file = discord.File(filepath, spoiler=False)
        await thread.send(file=file)
        # Add a delay between uploads to ensure original order of photos is preserved.
        await asyncio.sleep(1.0)

    await message.delete()


async def handle_video(message, parent_folder: str):
    """This method will download the video using youtube_dl,
    convert it to libx264 encoding to allow it to be embedded in discord,
    and upload it."""
    filepath = f"{parent_folder}/raw.mp4"
    # Try to download the video using youtube_dl
    ydl_opts = {
        "outtmpl": filepath,
        # 'merge_output_format': 'mp4',
        "retries": 3,
        "quiet": True,
        "verbose": False,  # Set to True to see output
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(message.content, download=False)
            video_name = info["title"].split("#")[0]
            video_name = "" if video_name == "" else f"> ||{video_name}||"
            ydl.download([message.content])

            # Convert the video to libx264 encoding (allows it to be embedded in discord)
            # The name of the video can be anything. Arbitrarily, the message ID was chosen.
            # It can be anything except the name of the raw, pre-conversion video.
            output_file = f"{parent_folder}/{message.id}.mp4"

            ffmpeg = (
                FFmpeg()
                .option("y")
                .input(filepath)
                .output(
                    output_file,
                    {"codec:v": "libx264", "codec:a": "copy"},
                    # vf="scale=1280:-1",
                    preset="medium",  # Valid presets are ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, and veryslow
                    crf=compression,  # 0 is lossless, 51 is worst quality
                )
            )

            # Run FFmpeg command
            try:
                await ffmpeg.execute()
                print("Conversion complete!")
            except Exception as e:
                print(f"Conversion failed with error: {e}")

            # If greater than 25MB, add a reaction and stop
            if os.path.getsize(filepath) > 25 * 10**6:
                await message.remove_reaction(emojis["wait_emoji"], client.user)
                print("File too large; aborting.")
                await message.add_reaction(emojis["too_large_emoji"])
                return

            file = discord.File(output_file)
            # Upload the file with the the author's name
            await message.channel.send(f"*{message.author.name}*:", file=file)
            # Delete the directory after sending it.
            # This deletes the file and parent folder
            await message.delete()

        except Exception as e:
            # raise(e)
            # Log specific errors
            if "404" in str(e):
                print("Error: 404 (video likely deleted)")
            # Log all other errors generically
            else:
                print(f"Error: {e}")

            await message.remove_reaction(emojis["wait_emoji"], client.user)
            await message.add_reaction(emojis["error_emoji"])


async def handle_link(message: discord.Message):
    await message.add_reaction(emojis["wait_emoji"])

    # Make the subdirectory for the slideshow/video
    # (if we don't, we'll get an error that the path doesn't exist)
    # handled at this level and not inside the functions because we need to delete the folder after
    parent_folder = f"downloads/{message.id}"
    os.mkdir(parent_folder)

    # If this is a slideshow, get the photos from the link
    html = requests.get(message.content).text
    if "i-photomode" in html:
        print("\tHandling slideshow")
        await handle_photo_slideshow(message, parent_folder)

    else:
        print("\tHandling video")
        await handle_video(message, parent_folder)

    shutil.rmtree(parent_folder)


async def handle_rescan(message: discord.Message):
    components = message.content.split(" ")
    # Use default_rs_count if no number is specified
    count = default_rs_count if len(components) == 1 else int(components[1])
    # Add one to the count to account for the rs command itself
    count += 1

    # Get messages from channel
    history = message.channel.history(limit=count)
    async for msg in history:
        # Skip messages that the bot sent
        if (not msg.author.bot) and ("tiktok.com" in msg.content):
            await handle_link(msg)

    await message.delete()


@client.event
async def on_message(message: discord.Message):
    # Check if the message is from a bot to avoid infinite loop
    if message.author.bot:
        return

    # If the message has "{prefix}ns" (No Scan), don't do anything.
    # This way people can link a video and not have it embedded.
    elif f"{prefix}ns" in message.content:
        print("Avoiding message")
        return

    # If the message has "{prefix}rs" (Rescan),
    # rehandle previous messages as specified by the user or 25 by default
    elif f"{prefix}rs" in message.content:
        print("Handling rescan")
        await handle_rescan(message)

    # Check if "tiktok.com" is in the message content
    elif "tiktok.com" in message.content:
        print(f"Handling link: {message.content}")
        await handle_link(message)

# Run the bot with your token
client.run(os.getenv("TOKEN"))
