# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report
from modelPredict import Predictor
import pdb


# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens['discord']


class ModBot(discord.Client):
    def __init__(self): 
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {} # Map from guild to the mod channel id for that guild
        self.reports = {} # Map from user IDs to the state of their report
        self.predictor = Predictor()
        self.concerns = {}

    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception("Group number not found in bot's name. Name format should be \"Group # Bot\".")

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). 
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel. 
        '''
        # Ignore messages from the bot 
        if message.author.id == self.user.id:
            return

        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild:
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)

    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.user.id:
            return
        channel = self.get_channel(payload.channel_id)
        if not channel:
            return
        if not channel.name == f'group-{self.group_num}-mod':
            return
        
        if self.get_guild(payload.guild_id):
            if str(payload.emoji.name) != '❌' and str(payload.emoji.name) != '👎':
                return
            message = await channel.fetch_message(payload.message_id)
            for author in self.reports:
                report = self.reports[author]
                if report.message.content in message.content:
                    await report.message.delete()
                    if str(payload.emoji.name) == '❌':
                        await report.message.channel.send(f"{report.message.author} has been removed from this channel")
                    self.reports.pop(author)
                    break

    async def handle_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply =  "Use the `report` command to begin the reporting process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id
        responses = []

        # Only respond to messages if they're part of a reporting flow
        if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)

        # Let the report class handle this message; forward all the messages it returns to us
        responses = await self.reports[author_id].handle_message(message)
        for r in responses:
            await message.channel.send(r)

        # If the report is complete or cancelled, remove it from our map
        if not self.reports[author_id].report_complete():
            return
        
        if not self.reports[author_id].awaiting_mod:
            if self.reports[author_id].send_to_mod:
                await self.send_reported_message(self.reports[author_id])

    async def send_reported_message(self, report):
        message = report.message
        mod_channel = self.mod_channels[message.guild.id]
        if report.danger == True:
            await mod_channel.send('This message was flagged as causing imminent danger to the user or other parties. Please follow the proper protocols and contact local authorities.')
        await mod_channel.send('If you would you like to remove this message, react with 👎')
        await mod_channel.send('If you like to remove this message and ban the user, react with ❌:')
        await mod_channel.send(message.content)
        report.awaiting_mod = True

    async def handle_channel_message(self, message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f'group-{self.group_num}':
            return

        # Forward the message to the mod channel
        mod_channel = self.mod_channels[message.guild.id]
        # await mod_channel.send(f'Forwarded message:\n{message.author.name}: "{message.content}"')
        classification = self.eval_text(message.content)[0]
        result = await self.code_format(classification, message)
        for msg in result:
            await mod_channel.send(msg)

    
    def eval_text(self, message):
        return self.predictor.svmPredict(message)

    
    async def code_format(self, classification, msg):
        result = []
        name = (msg.author.name)[:-1]
        if classification == "no risk":
            result.append("-------------------------------------")
            return []
        result.append(f"This message from '{name}' was evaluated to be " + classification + ".")
        author_id = msg.author.id

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)
            self.reports[author_id].message = msg

        if classification == 'high risk':
            result.append(f'Message: "{msg.content}"')
            result.append('It was flagged as causing imminent danger to the user or other parties. Please follow the proper protocols and contact local authorities.')
            result.append('The message was removed and the user placed on a temporary ban.')
            await msg.delete()
            await msg.channel.send(f"{name} has been placed on a temporary ban")
            safe_msg = ["I'm really sorry you're feeling this way.", "You're not alone, and there are people who care about you and want to help.", "If you're in immediate danger or need support, please reach out to a mental health professional or contact a crisis line in your area.", "For example, if you're in the U.S., you can call or text the 988 Suicide & Crisis Lifeline at 988 — it's free, confidential, and available 24/7."]
            for sentence in safe_msg:
                await msg.channel.send(sentence)
            self.reports.pop(author_id)
        elif classification == 'moderate risk':
            if msg.author.name not in self.concerns:
                self.concerns[msg.author.name] = {}
                self.concerns[msg.author.name]["counter"] = 0
                self.concerns[msg.author.name]["messages"] = []
            self.concerns[msg.author.name]["counter"] += 1
            self.concerns[msg.author.name]["messages"].append(msg.content)
            result.append('If you would you like to remove this message, react with 👎')
            result.append('If you like to remove this message and place this user on a temporary ban, react with ❌:')
            result.append(f'React to this message: "{msg.content}"')
            if self.concerns[msg.author.name]["counter"] >= 3:
                result.append("-------------------------------------")
                result.append(f"{name} has sent multiple messages consistent with moderate risk. Please review the following messages and escalate the concern if needed")
                for i in range(len(self.concerns[msg.author.name]["messages"])):
                    result.append(f'{i}. ' + '"' + self.concerns[msg.author.name]["messages"][i] + '"')
                # result.append('If you like to remove this message and place this user on a temporary ban, react with ❌:')
                # result.append(f'React to this message to place a ban on the user.')
        result.append("-------------------------------------")
        return result


client = ModBot()
client.run(discord_token)