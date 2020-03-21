#!/usr/bin/python

import time

from slackclient import SlackClient

from cthulhu_game import Icon

from cthulhu_game_bot_base import (
    BotBase,
    add_logging,
    add_cthulhu_handlers,
)

def convert_telegram_commands_to_slack_commands(text, botname):
    # all of the help text specifies commands as "/command", but in Slack we currently want to send commands as
    # "@bot_username command", so let's just alter the text directly until we either support slash commands in this bot
    # or tweak the help text to be platform-agnostic

    # TODO: make this even the slightest bit less silly in the future
    text = text.replace("/", "@" + botname + " ")

    return text


class SlackBot(BotBase):

    def __init__(self, token, username):
        # we need our token and our username
        self.client = SlackClient(token)
        self.username = username

        # get user name <--> ID mappings
        users = self.client.api_call("users.list").get("members")
        self.names_to_ids = {
            user.get("name"): user.get("id")
            for user in users
        }
        self.ids_to_names = {
            user.get("id"): user.get("name")
            for user in users
        }
        self.user_id = self.names_to_ids[self.username]

        # we're going to maintain chat data ourselves, unlike telegram which sends it around
        self.chat_data = {}

        # we're going to keep a map of (keyword --> handler)
        self.handlers = {}

    def get_icon_map(self):
        # slack uses slack emojis
        return {
            Icon.FLASHLIGHT: ":flashlight:",
            Icon.HIDDEN: ":black_circle:",
            Icon.BLANK: ":white_circle:",
            Icon.SIGN: ":large_blue_circle:",
            Icon.CTHULHU: ":red_circle:",
        }

    def tag_user(self, chat_id, user_id, name):
        return self.send_message(chat_id, "{} (<@{}>)".format(name, user_id))

    def send_message(self, chat, text, markdown=False, **kwargs):
        # convert text of telegram commands into slack commands
        text = convert_telegram_commands_to_slack_commands(text, self.username)

        self.client.api_call(
            "chat.postMessage",
            channel=chat,
            text=text,
            as_user=True)

    def add_handler(self, fn, *keywords, **kwargs):
        # extract relevant kwargs
        pass_chat_data = kwargs.get("pass_chat_data", False)
        pass_args = kwargs.get("pass_args", False)

        # add the handler to our map, for each keyword
        for keyword in keywords:
            self.handlers[keyword] = (fn, pass_chat_data, pass_args)

    def run(self):
        """ Python slackbot is a continuous process which watches for messages, so we need to start that process for
        anything to actually work """

        # TODO: use the new form of slackbot involving a RESTful server which watches rather than this while loop, and
        # authenticates via OAuth, and real slash commands, and all that other fancy stuff

        print("Attempting Slack Connection...")
        if self.client.rtm_connect():
            print("Successful Connection!")
        else:
            print("Connection Failed :(")

        while True:
            time.sleep(1)
            for message in self.client.rtm_read():
                try:
                    # parse the message
                    text = message.get("text", "")

                    if not text:
                        continue

                    words = text.split()

                    # if the message for us?
                    if words[0] == "<@{}>".format(self.user_id):
                        # is the message a command?
                        command = words[1] if len(words) > 1 else None
                        if command in self.handlers:
                            # get the handler function, and whether or not we want to pass chat data and args
                            fn, pass_chat_data, pass_args = self.handlers[command]

                            # get the channel and the sender information of the message
                            chat = message.get("channel")
                            sender_id = message.get("user")
                            sender_name = self.ids_to_names[sender_id]

                            # we're building a kwargs dict to pass to our function
                            fn_kwargs = {
                                "chat_id": chat,
                                "user_id": sender_id,
                                "user_name": sender_name,
                            }

                            # we may or may not want to pass chat_data and args
                            if pass_chat_data:
                                fn_kwargs["chat_data"] = self.chat_data
                            if pass_args:
                                # pass everything after the command
                                fn_kwargs["args"] = words[2:]

                            # actually call the function
                            fn(self, **fn_kwargs)
                except Exception as e:
                    print("found exception: {}".format(str(e)))


def run_cthulhu_slack():
    # set up the bot, reading the token and username information from git-ignored files
    with open("ignore/slack_token.txt") as f:
        token = f.read().strip()
    with open("ignore/slack_username.txt") as f:
        botname = f.read().strip()
    bot = SlackBot(token, botname)

    # add logging and our cthulhu handlers
    add_logging()
    add_cthulhu_handlers(bot)

    # start running the bot
    bot.run()


# actually run things
if __name__ == '__main__':
    run_cthulhu_slack()
