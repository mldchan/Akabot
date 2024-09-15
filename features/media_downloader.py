### Media Downloader: Use Cobalt.tools to download media and repost it as files.
### THIS REQUIRES MESSAGE CONTENT INTENT FOR IT TO WORK!

import json
import os
import random
import re

import discord
import requests

api_list = []

with open("configs/media_downloader.json") as f:
    data = json.load(f)
    api_list = data["apiList"]
    if "videoQuality" in data:
        video_quality = data["videoQuality"]
    else:
        video_quality = "360"

    if "audioQuality" in data:
        audio_quality = data["audioQuality"]
    else:
        audio_quality = "64"

    if "maxUploadSize" in data:
        max_upload_size = data["maxUploadSize"]
    else:
        max_upload_size = "25m"

    if video_quality not in ["360", "480", "720", "1080"]:
        video_quality = "360"

    if audio_quality not in ["64", "96", "128", "256"]:
        audio_quality = "64"

    if max_upload_size.endswith("m"):
        max_upload_size = int(max_upload_size[:-1]) * 1024 * 1024
    elif max_upload_size.endswith("k"):
        max_upload_size = int(max_upload_size[:-1]) * 1024
    else:
        max_upload_size = int(max_upload_size)


class MediaDownloader(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        super().__init__()
        self.bot = bot

    @discord.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        urls = [x for x in msg.content.split(" ") if re.match(r'https?://[\da-z\.-]+\.[a-z\.]{2,6}[\/\w \.-]*\/?', x)]
        if not urls:
            return

        first_url = urls[0]

        details = requests.post(random.choice(api_list), headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        }, json={
            "url": first_url,
            "filenameStyle": "pretty",
            "alwaysProxy": True,
            "videoQuality": video_quality,
            "audioBitrate": audio_quality
        })

        if not details.ok:
            print("Not OK")
            return

        details = details.json()

        if details['status'] == "error":
            print("Error", details)
            return

        if details['status'] == "redirect":
            with open(details['filename'], "wb") as f:
                f.write(requests.get(details['url']).content)

            if os.path.exists(details['filename']) and os.path.getsize(details['filename']) > 0 and os.path.getsize(details['filename']) < max_upload_size:
                await msg.reply(file=discord.File(details['filename']))
                os.remove(details['filename'])

        if details['status'] == 'tunnel':
            with open(details['filename'], "wb") as f:
                f.write(requests.get(details['url']).content)

            if os.path.exists(details['filename']) and os.path.getsize(details['filename']) > 0 and os.path.getsize(details['filename']) < max_upload_size:
                await msg.reply(file=discord.File(details['filename']))
                os.remove(details['filename'])

        if details['status'] == "picker":
            files_to_upload = []
            if details['audio']:
                with open(details['audio_filename'], "wb") as f:
                    print("Downloading audio", details['audio'])
                    f.write(requests.get(details['url']).content)
                    files_to_upload.append(discord.File(details['audio']))

            for i, v in enumerate(details['picker']):
                with open(v['type'] + str(i) + ".jpeg", "wb") as f:
                    print("Downloading", v['url'], "media", i)
                    f.write(requests.get(v['url']).content)
                    files_to_upload.append(discord.File(v['type'] + str(i) + ".jpeg"))

            await msg.reply(files=files_to_upload)
