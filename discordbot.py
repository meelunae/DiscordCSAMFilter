import datetime
import discord
from discord.ext import commands
import io
import numpy as np
from mongoengine import *
from PIL import Image
import pytesseract
import requests
import uuid
import yaml

class Reports(Document):
    reportId = IntField(required=True)
    serverName = StringField(max_length=100,required=True)
    userId = IntField(required=True)
    imageText = StringField(max_length=1337,required=True)


TOKEN = 'token_here'
bot = commands.Bot(command_prefix='cs!')
config = yaml.load(open("config.yaml"), Loader=yaml.FullLoader)
connect('csampolicebot', host='127.0.0.1', port=27017)

def is_staff():
    def predicate(ctx):
        return ctx.message.guild.get_role(config["moderation_role_ID"]) in ctx.message.author.roles
    return commands.check(predicate)

def is_owner():
    def predicate(ctx):
        return ctx.author.id == 1337 # to be replaced with bot/server owner ID
    return commands.check(predicate)

@bot.event
async def on_ready():
    print('Successfully connected! Hello!')

@bot.event
async def on_message(message):
    staff_role = message.guild.get_role(config["moderation_role_ID"])       
    if not staff_role in message.author.roles:
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
                result, text = scancontent(url)
                if result:
                    user = message.author
                    role = message.guild.get_role(config["punished_role_ID"])
                    report_id = uuid.uuid1().int>>65
                    channel = bot.get_channel(config["alert_channel"])
                    embed = discord.Embed(title="User muted", description="", color=0x00ff00)
                    embed.add_field(name="User", value="{} <\@{}>".format(user, user.id), inline=False)
                    embed.add_field(name="Reason", value="Blacklisted word detected in image", inline=False)
                    embed.add_field(name="Mute ID", value="{}".format(report_id), inline=False)
                    embed.timestamp = datetime.datetime.utcnow()
                    report = Reports(reportId=report_id, serverName=message.guild.name, userId=user.id, imageText=text)
                    report.save()
                    await channel.send(embed=embed)
                    await user.add_roles(role)
                    await message.delete()
    await bot.process_commands(message)

@bot.command()
@is_owner()
async def delete(ctx, rID):
    try:
        report = Reports.objects.get(reportId=rID)
        report.delete()
        msg = discord.Embed(title="Report deletion", description="", color=0x00ff00)
        msg.add_field(name=":white_check_mark: Success", value="The report indicated by you has been deleted successfully.", inline=False)
        msg.timestamp = datetime.datetime.utcnow()
    except Reports.DoesNotExist:
        msg = discord.Embed(title="Report deletion", description="", color=0x00ff00)
        msg.add_field(name=":x: Something's wrong!", value="Sorry! I couldn't find any reports to delete for the ID you provided.", inline=False)
        msg.timestamp = datetime.datetime.utcnow()
    await ctx.send(embed=msg)


@bot.command()
@is_staff()
async def lookup(ctx, rID):
    try:
        report = Reports.objects.get(reportId=rID)
        user =  await bot.fetch_user(report.userId)
        msg = discord.Embed(title="Report information", description="", color=0x00ff00)
        msg.add_field(name="User", value="{} <\@{}>".format(user, user.id), inline=False)
        msg.add_field(name="Server", value="{}".format(report.serverName), inline=False)
        msg.add_field(name="Reported image content", value=report.imageText, inline=False)
        msg.timestamp = datetime.datetime.utcnow()
    except Reports.DoesNotExist:
        report = None
        msg = discord.Embed(title="Report information", description="", color=0x00ff00)
        msg.add_field(name="No report found :(", value="Sorry! I couldn't find any reports for the ID you provided.", inline=False)
        msg.timestamp = datetime.datetime.utcnow()
    await ctx.send(embed=msg)

def scancontent(url):
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content))
        image =  np.array(im)
        text = pytesseract.image_to_string(image)
        # Freeing memory because we don't need the image anymore, text is enough
        im.close()
        image = None
        for word in config["banned_words"]:
            if word in text.lower():
                return True, text
    except requests.exceptions.HTTPError as err:
        print(err)
    return False, text

def main():
    bot.run(TOKEN)

if __name__ == '__main__':
    main()