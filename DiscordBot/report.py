from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    REPORT_COMPLETE = auto()

class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
        self.send_to_mod = False
        self.awaiting_mod = False
        self.danger = False
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return ["Report cancelled."]
        
        if self.state == State.REPORT_START:
            reply =  "Thank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            self.state = State.AWAITING_MESSAGE
            return [reply]
        
        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED
            self.message = message
            return ["I found this message:", "```" + message.author.name + ": " + message.content + "```", "Is this a 'user' or 'LLM' message?"]
        
        if self.state == State.MESSAGE_IDENTIFIED:
            if message.content == 'bypass':
                self.send_to_mod = True
                self.danger = True
                self.state = State.REPORT_COMPLETE
                return ["Message forwarded"]
            if message.content == 'user':
                return ["Please select a reason for reporting this message:", "Offensive Content", "Imminent Danger", "Criminal Activity"]
            if message.content == 'LLM':
                return ["Thank you for reporting, we've sent this to our moderator team!"]
            # if "kill my self" in message.content.lower() or "kms" in message.content.lower(): 
            #     return  + ["This message contains harmful langauge and will be removed!"]
            if message.content == "Offensive Content":
                return ["Please select the type of offensive content:", "Sexual Content", "Hate Speech or Discrimination", "Violent or Gory Language"]
            if message.content == "Imminent Danger":
                return ["Please select the type of imminent danger:", "Self Harm", "Suicide", "Risky Behavior"]
            if message.content == "Criminal Activity":
                return ["Please select the type of criminal activity:", "Violence toward others", "Designing Scams", "Theft", "Terrorism"]
            if message.content == "Sexual Content":
                return ["Please select the type of sexual content:", "Sexual relationship with chatbot", "Graphic sexual descriptions", "Sexual violence"]
            if message.content == "Hate Speech or Discrimination":
                return ["Please select the type of hate speech or discrimination:", "Racism", "Misogyny", "Homophobia", "Transphobia"]
            if message.content == "Violent or Gory Language":
                return ["Please select the type of violent or gory language:", "Animal harm", "Human body mutilation"]
            if message.content ==  "Self Harm":
                return ["Please select method of self harm discussed:", "Cutting", "Self-starvation", "Self-violence", "Other", "Unknown"]
            if message.content == "Suicide":
                return ["Please select method of suicide discussed:", "Firearm", "Drug overdose", "Motor vehicle accident", "Other", "Unknown"]
            if message.content == "Risky behavior":
                return ["Please select type of risky behavior discussed:", "Drug abuse", "Risky stunts", "Other", "Unknown"]
            if message.content == "Violence toward others" or message.content == \
            "Designing Scams" or message.content == "Theft" or message.content == "Terrorism" or \
            message.content == "Sexual violence" or message.content == "Violence toward others" or \
            message.content == "Cutting" or message.content == "Self-starvation" or message.content == "Self-violence" or \
            message.content == "Other" or message.content == "Unknown" or \
            message.content == "Firearm" or message.content == "Drug overdose" or \
            message.content == "Motor vehicle accident" or message.content == "Drug abuse" or \
            message.content == "Risky stunts" or message.content == "Animal harm" or \
            message.content == "Human body mutilation":
                return ["Does the user have specific plans or serious intentions of carrying out this act?", "Yes", "No", "Unsure"]
            if message.content == "Yes":
                self.state = State.REPORT_COMPLETE
                self.send_to_mod = True
                self.danger = True
                return ["Thank you for letting us know. Please call 911 immediately to report the information you have, and we will also work to ensure the safety of the vulnerable parties."]
            if message.content == "No" or message.content == "Unsure" or message.content == "Racism" or \
            message.content == "Misogyny" or message.content == "Homophobia" or \
            message.content == "Transphobia" or message.content == "Sexual relationship with chatbot" or \
            message.content == "Graphic sexual descriptions":
                self.state = State.REPORT_COMPLETE
                self.send_to_mod = True
                return ["Thank you for letting us know. We take this concern seriously and will follow up with the user."]
            if message.content == "report":
                self.state = State.REPORT_START
                return await self.handle_message(message)

            return ["Please enter a valid response or type 'cancel' to end your report. Remember that responses are case-sensitive."]

        return []

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    


    

