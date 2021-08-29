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
    print('Logged in as {bot.user}') 

@bot.event
async def on_message(message):
    if message.attachments:
        for ext in pic_ext:
            if message.attachments[0].url.endswith(ext):
                im = Image.open(requests.get(message.attachments[0].url, stream=True).raw)
                image =  np.array(im)
                text = pytesseract.image_to_string(image)
                print(text)
                for word in wordlist["banned_words"] :
                    if word in text:
                        print("Found CP mention, get yeeted!")
                        await message.author.ban(reason = "Suspected CSAM invite. Appeal if this is not the case.")
                        await message.delete()
    
bot.run('token')
