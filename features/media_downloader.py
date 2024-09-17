### Media Downloader: Use Cobalt.tools to download media and repost it as files.
### THIS REQUIRES MESSAGE CONTENT INTENT FOR IT TO WORK!

import json
import math
import os
import random
import re

import discord
import requests
from discord.ext import commands

from utils.settings import get_setting, set_setting

api_list = []

svc_tips = [
    "Append -a to download audio only (Great for music).",
    "Append -o to remove sound from video and only keep music (TikTok only).",
    "Music channels only: When in music mode, only music will be downloaded."
]

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

    if audio_quality not in ["64", "96", "128", "256", "320"]:
        audio_quality = "128"

    if max_upload_size.endswith("m"):
        max_upload_size = int(max_upload_size[:-1]) * 1024 * 1024
    elif max_upload_size.endswith("k"):
        max_upload_size = int(max_upload_size[:-1]) * 1024
    else:
        max_upload_size = int(max_upload_size)


def get_random_tip():
    return random.choice(svc_tips)


class MediaDownloader(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        super().__init__()
        self.bot = bot

    server_info = {}

    @discord.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if not get_setting(msg.guild.id, f'{msg.channel.id}_media_downloader_enabled', 'false') == 'true':
            return

        if msg.author.bot:
            return

        urls = [x for x in msg.content.split(" ") if re.match(r'https?://[\da-z\.-]+\.[a-z\.]{2,6}[\/\w \.-]*\/?', x)]

        if not urls:
            if get_setting(msg.guild.id, f'{msg.channel.id}_media_downloader_verbose', 'false') == 'true':
                await msg.reply("Could not find any links in the message.\n-# " + get_random_tip())
            return

        if msg.guild.id in self.server_info and self.server_info[msg.guild.id] == "processing":
            if get_setting(msg.guild.id, f'{msg.channel.id}_media_downloader_verbose', 'false') == 'true':
                await msg.reply("Can't download right now. Please wait for the other download to finish.\n-# " + get_random_tip())
            return

        self.server_info[msg.guild.id] = "processing"

        first_url = urls[0]

        audio_only = "-a" in msg.content or get_setting(msg.guild.id, f'{msg.channel.id}_media_downloader_music', 'false') == 'true'
        original_audio = "-o" in msg.content

        message = None
        if get_setting(msg.guild.id, f'{msg.channel.id}_media_downloader_verbose', 'false') == 'true':
            mode = "(Audio only)" if audio_only else ""
            mode += " (Original audio (TikTok))" if original_audio else ""
            message = await msg.reply("Requesting download... " + mode + "\n-# " + get_random_tip())

        instance = random.choice(api_list)

        json_data = {
            "url": first_url,
            "filenameStyle": "pretty",
            "alwaysProxy": True,
            "videoQuality": video_quality,
            "audioBitrate": audio_quality
        }

        if audio_only:
            json_data["downloadMode"] = "audio"

        if original_audio:
            json_data['tiktokFullAudio'] = True

        details = requests.post(instance, headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        }, json=json_data)

        if not details.ok:
            if message:
                await message.edit(content="There was an error downloading the media. Server returned a non-2xx status code.\n-# " + get_random_tip())
                await message.delete(delay=5)
            del self.server_info[msg.guild.id]
            return

        details = details.json()

        if details['status'] == "error":
            if message:
                await message.edit(content="There was an error downloading the media. Service returned an error.\n-# " + get_random_tip())
                await message.delete(delay=5)
            del self.server_info[msg.guild.id]
            return

        if details['status'] == "redirect" or details['status'] == "tunnel":
            await message.edit(content=f"Downloading {details['filename']}...\n-# " + get_random_tip())
            with open(details['filename'], "wb") as f:

                f.write(requests.get(details['url']).content)

            if os.path.exists(details['filename']) and 0 < os.path.getsize(details['filename']) < max_upload_size:
                await message.edit(
                    content=f"Uploading {details['filename']} ({math.floor(os.path.getsize(details['filename']) / 1024)}KB / {math.floor(max_upload_size / 1024)}KB)...\n-# " + get_random_tip())
                await msg.reply(file=discord.File(details['filename']))
                os.remove(details['filename'])
                await message.edit(content="Done processing.\n-# " + get_random_tip())
                await message.delete(delay=5)
            elif os.path.getsize(details['filename']) > max_upload_size:
                await message.edit(content=f"File too large ({os.path.getsize(details['filename'])} > {max_upload_size})\n-# " + get_random_tip())
                os.remove(details['filename'])
                await message.edit(content="Done processing.\n-# " + get_random_tip())
                await message.delete(delay=5)
            del self.server_info[msg.guild.id]
            return

        if details['status'] == "picker":
            await message.edit(content="Downloading media...\n-# " + get_random_tip())

            files_downloaded = []
            files_to_upload = []
            if details['audio']:
                if message:
                    await message.edit(content="Attempting to download audio...\n-# " + get_random_tip())
                with open(details['audioFilename'], "wb") as f:

                    f.write(requests.get(details['audio']).content)
                    files_downloaded.append(details['audioFilename'])
                    if os.path.exists(details['audioFilename']) and 0 < os.path.getsize(details['audioFilename']) < max_upload_size:
                        files_to_upload.append(discord.File(details['audioFilename']))

            for i in range(0, len(details['picker']), 9):
                curr_files_to_upload = []
                for j, v in enumerate(details['picker'][i:i + 9]):
                    file_name = v['type'] + str(i + j) + ".jpeg"
                    with open(file_name, "wb") as f:

                        await message.edit(content=f"Downloading {i + j}/{len(details['picker'])}...\n-# " + get_random_tip())
                        f.write(requests.get(v['url']).content)
                        files_downloaded.append(file_name)
                        if os.path.exists(file_name) and 0 < os.path.getsize(file_name) < max_upload_size:
                            curr_files_to_upload.append(discord.File(file_name))

                await message.edit(content=f"Uploading media {i + 1}-{i + 9}/{len(details['picker'])}...\n-# " + get_random_tip())
                await msg.reply(files=curr_files_to_upload)

            await message.edit(content="Finished uploading media. Done processing.\n-# " + get_random_tip())
            for file in files_downloaded:
                os.remove(file)
            await message.delete(delay=5)
            del self.server_info[msg.guild.id]

    media_downloader_group = discord.SlashCommandGroup(name="media_downloader", description="Media downloader settings")

    @media_downloader_group.command(name="enabled", description="Set if the media downloader is enabled in this channel.")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def enabled(self, ctx: discord.ApplicationContext, enabled: bool):
        set_setting(ctx.guild.id, f"{ctx.channel.id}_media_downloader_enabled", str(enabled).lower())
        await ctx.respond("Set enabled to " + str(enabled) + " in this channel.", ephemeral=True)

    @media_downloader_group.command(name="verbose", description="Set if the media downloader should be verbose.")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def verbose(self, ctx: discord.ApplicationContext, verbose: bool):
        set_setting(ctx.guild.id, f"{ctx.channel.id}_media_downloader_verbose", str(verbose).lower())
        await ctx.respond("Set verbose to " + str(verbose) + " in this channel.", ephemeral=True)

    @media_downloader_group.command(name="music", description="Set if the media downloader should be in music mode.")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def is_music_channel(self, ctx: discord.ApplicationContext, music_mode: bool):
        set_setting(ctx.guild.id, f"{ctx.channel.id}_media_downloader_music", str(music_mode).lower())
        await ctx.respond("Set is music channel to " + str(music_mode) + " in this channel.", ephemeral=True)
