import discord
from discord.ext import commands
from PIL import Image
import numpy as np
import io
import requests
import yaml
import pytesseract

bot = commands.Bot(command_prefix='!')
wordlist_file = open("wordlist.yaml")
wordlist = yaml.load(wordlist_file, Loader=yaml.FullLoader)

@bot.event
async def on_ready():
    print('Successfully connected! Hello!') 

@bot.event
async def on_message(message):
    
    urls = set()

    for part in message.content.lower().split():
        if part.startswith("http") and (part.endswith(".jpg") or part.endswith(".png") or part.endswith(".jpeg")):
            urls.add(part)

    if message.attachments:
        for attachment in message.attachments:
            # just like embeds, attachments that are not images do not interest us so we won't add them to the URL list to scan
            if attachment.url.lower().endswith(".jpg") or attachment.url.lower().endswith(".png") or attachment.url.lower().endswith(".jpeg"):
                urls.add(attachment.url) 

    if len(urls) > 0:
        for url in urls:
            if scancontent(url):
                print("Found blacklisted word mention, get yeeted!")
                user = message.author
                role = message.guild.get_role(wordlist["punished_role_ID"])
                channel = bot.get_channel(wordlist["alert_channel"])
                embed = discord.Embed(title="User muted", description="", color=0x00ff00)
                embed.add_field(name="User", value="{} <\@{}>".format(user, user.id), inline=False)
                embed.add_field(name="Reason", value="Blacklisted word detected in image", inline=False)
                await channel.send(embed=embed)
                await user.add_roles(role)
                await message.delete()


def scancontent(url):
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content))
        image =  np.array(im)
        text = pytesseract.image_to_string(image)
        for word in wordlist["banned_words"]:
            if word in text.lower():
                return True
    except requests.exceptions.HTTPError as err:
        print(err)
        return False


bot.run('token')