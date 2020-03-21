import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler


from cthulhu_game import Icon

from cthulhu_game_bot_base import (
    BotBase,
    add_logging,
    add_cthulhu_handlers,
)

class TelegramBot(BotBase):

    def __init__(self, token):
        # start the internal telegram bot
        self.bot = telegram.Bot(token=token)

        # Create an updater to fetch updates.
        updater = Updater(token=token)

        self.dispatcher = updater.dispatcher

    def get_icon_map(self):
        # telegram uses emojis because sure
        return {
            Icon.FLASHLIGHT: "🔦",
            Icon.HIDDEN: "⚫",
            Icon.BLANK: "⚪️",
            Icon.SIGN: "🔵",
            Icon.CTHULHU: "🔴",
        }

    def tag_user(self, chat_id, user_id, name):
        return self.send_message(chat_id, "[{}](tg://user?id={})".format(name, player_id), markdown=True)

    def send_message(self, chat, text, markdown=False, **kwargs):
        telegram_kwargs = {
            'chat_id': chat,
            'text': text,
        }
        if markdown:
            telegram_kwargs['parse_mode'] = telegram.ParseMode.MARKDOWN
        return self.bot.send_message(**telegram_kwargs)

    def add_handler(self, fn, *keywords, **outer_kwargs):
        pass_chat_data = outer_kwargs.get("pass_chat_data", False)
        pass_args = outer_kwargs.get("pass_args", False)

        # Telegram expects handler functions in a different way, so let's make a wrapper
        def wrapper(bot, update, **kwargs):
            # build up the keyword arguments we're passing
            fn_kwargs = {}

            # update will contain the message info
            fn_kwargs["chat_id"] = update.message.chat_id
            fn_kwargs["user_id"] = update.message.from_user.id
            fn_kwargs["user_name"] = update.message.from_user.first_name

            # we may or may not pass chat_data and args as keyword arguments
            keys_to_pass = [
                (pass_chat_data, "chat_data"),
                (pass_args, "args"),
            ]
            for (should_pass, key) in keys_to_pass:
                if should_pass:
                    fn_kwargs[key] = kwargs.get(key, None)

            # return the actual function
            return fn(bot, **fn_kwargs)

        # if only one keyword, telegram expects it as a single string
        if len(keywords) == 1:
            keywords = keywords[0]

        # create the CommandHandler and add it to our dispatcher
        telegram_handler = CommandHandler(keywords, wrapper, pass_chat_data=pass_chat_data, pass_args=pass_args)
        self.dispatcher.add_handler(telegram_handler)


def run_cthulhu_telegram():
    # Set up the bot.
    # If you want to use this bot yourself, please message me directly.
    token = open('ignore/token.txt', 'r').read()
    bot = TelegramBot(token)

    add_logging()
    add_cthulhu_handlers(bot)


# Actually run Cthulhu Telegram Bot
if __name__ == '__main__':
    run_cthulhu_telegram()
