import discord
import io
from discord.ext import commands
from PIL import Image
import requests
import numpy as np
import yaml
import pytesseract

bot = commands.Bot(command_prefix='!')
pic_ext = ['.jpg','.png','.jpeg']
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
            urls.add(attachment.url)

    if len(urls) > 0:
        for url in urls:
            if scancontent(url):
                print("Found CP mention, get yeeted!")
                user = message.author
                role = discord.utils.get(message.guild.roles, name=wordlist["muted_role"])
                channel = bot.get_channel(wordlist["alert_channel"])
                embed = discord.Embed(title="User muted", description="", color=0x00ff00)
                embed.add_field(name="User", value=user, inline=False)
                embed.add_field(name="Reason", value="Suspected CSAM invite", inline=False)
                await channel.send(embed=embed)
                await user.add_roles(role)
                await message.delete()


def scancontent(url):
                    im = Image.open(requests.get(url, stream=True).raw)
                    image =  np.array(im)
                    text = pytesseract.image_to_string(image)
                    for word in wordlist["banned_words"]:
                        if word in text.lower():
                            return True
                    return False


bot.run('token')
