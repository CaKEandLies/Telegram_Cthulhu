# -*- coding: utf-8 -*-
"""
Created on Wed Mar 21 14:48:01 2018

@author: Amrita

This program implements a Telegram bot for games of Don't Mess With Cthulhu.

TODO:
    Implement a claims system.
    Implement a pending players command so that people can see who's signed up.
    Write more detailed messages in response to commands.
    Write flavortext.
    Potentially implement a spectate command.
    Rename both this module and the other.
"""

import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging
import cthulhu_game as cg

# Set up the bot and print out token info to ensure functionality.
token = '529296289:AAG6DixRzzbWYJKxuiopyCaSYmLmvnv5-PY'
bot = telegram.Bot(token=token)
print(bot.get_me())

# Create an updater to fetch updates.
updater = Updater(token=token)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)  # TODO: fix this line.


def start(bot, update):
    """
    Prints out a message detailing the functionality of this bot.
    """
    start_message = open('start.txt', 'r').read()
    bot.send_message(chat_id=update.message.chat_id, text=start_message)


def help_message(bot, update):
    """
    Sends the user a message giving help.

    #TODO: write this function.
    """
    bot.send_message(chat_id=update.message.chat_id,
                     text=read_message('messages/help.txt'))


def rules(bot, update):
    """
    Sends a message detailing the rules of the game.
    """
    bot.send_message(chat_id=update.message.chat_id,
                     text=read_message('messages/rules.txt'))


def wee(bot, update):
    """
    Replies with a hoo command.
    """
    bot.send_message(chat_id=update.message.chat_id, text="/hoo")


def hoo(bot, update):
    """
    Replies with a wee command.
    """
    bot.send_message(chat_id=update.message.chat_id, text="/wee")


def hi(bot, update):
    """
    Replies with a hi command.
    """
    bot.send_message(chat_id=update.message.chat_id, text="/hi")


def read_message(filepath):
    """
    Opens and returns a text file as a string.
    """
    message = open(filepath, 'r').read()
    return message


def new_game(bot, update, chat_data=None):
    """
    Starts a new game of Don't Mess with Cthulhu in the given chat.

    # TODO: Ensure in a chat with enough people.
    """
    if "game_is_ongoing" not in chat_data:
        chat_data["game_is_ongoing"] = False
        chat_data["game_is_pending"] = True
        chat_data["pending_players"] = {}
        bot.send_message(chat_id=update.message.chat_id,
                         text="/joingame to join, /startgame to start.")
    else:
        if chat_data["game_is_ongoing"]:
            bot.send_message(chat_id=update.message.chat_id,
                             text="There's already a game ongoing. /endgame?")
        elif chat_data["game_is_pending"]:
            bot.send_message(chat_id=update.message.chat_id,
                             text="There's already a game pending. /endgame?")
        else:
            chat_data["pending_players"] = {}
            chat_data["game_is_pending"] = True
            chat_data["game_is_ongoing"] = False
            bot.send_message(chat_id=update.message.chat_id,
                             text="/joingame to join, /startgame to start.")


def join_game(bot, update, chat_data=None, args=None):
    """
    Allows players to join a game of Don't Mess with Cthulhu in the chat.
    """
    if ("game_is_pending" not in chat_data) or not (chat_data["game_is_pending"]):
        bot.send_message(chat_id=update.message.chat_id, 
                         text="No game is pending!")
        return
    if len(chat_data["pending_players"]) >= 10:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Game is full, sorry!")
        return
    
    # Add this player to the list of pending players with a nickname.
    if args:
        nickname = args[0]
    else:
        nickname = update.message.from_user.first_name
    user_id = update.message.from_user.id
    chat_data["pending_players"][user_id] = nickname
    bot.send_message(chat_id=update.message.chat_id,
                     text="Registered under nickname %s!"%nickname)


def start_game(bot, update, chat_data=None):
    """
    Starts the pending game.
    
    #TODO: Fixes key error.
    """
    if "game_is_pending" not in chat_data:
        bot.send_message(chat_id=update.message.chat_id,
                         text="No game pending!")
    if chat_data["game_is_pending"]:
        if len(chat_data["pending_players"]) < 1:
            bot.send_message(chat_id=update.message.chat_id,
                             text="Not enough players yet!")
        else:
            chat_data["game_is_ongoing"] = True
            chat_data["game_is_pending"] = False
            chat_data["game"] = cg.Game(chat_data["pending_players"])
            begin_game(bot, chat_data["game"])
            bot.send_message(chat_id=update.message.chat_id,
                             text=chat_data["game"].display_board())
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="No game pending!")


def claim(bot, update):
    """
    Allows players to declare their claims.
    
    # TODO: Limit this to the player who can claim.
    # TODO: Write this function.
    """
    keyboard = [InlineKeyboardButton("1", callback_data='1')]
    pass


def send_roles(bot, game):
    """
    Sends roles to players in the game.
    """
    roles = game.get_roles()
    for user_id, is_cultist in roles.items():
        if is_cultist:
            bot.send_message(chat_id=user_id, text="You're a Cultist.")
        else:
            bot.send_message(chat_id=user_id, text="You're an Investigator.")


def send_hands(bot, game):
    """
    Sends hands to players in the game.
    """
    hands = game.get_hands()
    print(hands)
    for user_id, hand in hands.items():
        bot.send_message(chat_id=user_id, text=("You have %s blanks, %s signs"
                                                " and %s Cthulhus." % hand))


def new_round(bot, game, chat_data):
    """
    Collects cards at the end of the round, reshuffles them, and redeals them.
    """
    discovered = chat_data["discovered_this_round"]
    game.recollect_cards(discovered)
    game.deal_cards()
    send_hands(bot, game)
    chat_data["discovered_this_round"] = []
    chat_data["round_number"] = 1


def begin_game(bot, game):
    """
    Runs a game.
    """
    send_roles(bot, game)
    game.deal_cards()
    send_hands(bot, game)
    print(game.where_flashlight())


def can_investigate(bot, user_id, game):
    """
    Checks whether the user at that id can investigate others.
    """
    return game.get_position(player_id=user_id) == game.where_flashlight()


def investigate(bot, update, chat_data=None, args=None):
    """
    Allows players to investigate others. Returns False on failure.
    # TODO: Write this function.
    # TODO: check if game is ongoing.
    # TODO: clean up this entire fucking function. 
    """
    if "game_is_ongoing" not in chat_data:
        bot.send_message(chat_id=update.message.chat_id, text="No game going!")
        return False
    elif not chat_data["game_is_ongoing"]:
        bot.send_message(chat_id=update.message.chat_id, text="No game going!")
        return False
    if len(args) < 1:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Format: '/investigate name' "
                         " Want to try that again?")
        return False
    if not can_investigate(bot, update.message.from_user.id,
                           chat_data["game"]):
        bot.send_message(chat_id=update.message.chat_id,
                         text="You don't have the flashlight, dummy!")
        return False
    name = args[0] 
    pos = chat_data["game"].is_valid_name(name)
    if pos == -1:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Invalid input. Try again!")
        return False
    if not chat_data["game"].can_investigate_position(pos):
        bot.send_message(chat_id=update.message.chat_id,
                         text="You cannot investigate this player. Try again!")
        return False
    
    result, end_of_round = chat_data["game"].investigate(pos)
    if "E" in result:
        bot.send_message(chat_id=update.message.chat_id,
                         text="You found an Elder Sign!")
        if chat_data["game"].investigators_have_won():
            bot.send_message(chat_id=update.message.chat_id,
                             text="Investigators win!")
            end_game(bot, update, chat_data=chat_data)
            return True
    elif "C" in result:
        bot.send_message(chat_id=update.message.chat_id,
                         text="You found Cthulhu!")
        end_game(bot, update, chat_data)
        return True
    elif "-" in result:
        bot.send_message(chat_id=update.message.chat_id, text="Nothing...")

    if end_of_round:
        bot.send_message(chat_id=update.message.chat_id, 
                         text="Round is over!")
        chat_data["round_number"] += 1
        if chat_data["round_number"] > 4:
            bot.send_message(chat_id=update.message.chat_id,
                             text="Cultists win by default!")
            return True
        send_hands(bot, chat_data["game"])
    bot.send_message(chat_id=update.message.chat_id,
                     text=chat_data["game"].display_board())


def send_dm(bot, update):
    """
    Sends a test message directly to the user.
    """
    bot.send_message(chat_id=update.message.from_user.id,
                     text="sliding into those dungeon masters!")


def end_game(bot, update, chat_data=None):
    chat_data["game_is_pending"] = False
    chat_data["game_is_ongoing"] = False
    chat_data["game"] = None
    chat_data["pending_players"] = {}
    bot.send_message(chat_id=update.message.chat_id, text="ended!")
  

def cancel_game(bot, update, chat_data=None):
    end_game(bot, update, chat_data=chat_data)


start_handler = CommandHandler('start', start)
wee_handler = CommandHandler('wee', wee)
hoo_handler = CommandHandler('hoo', hoo)
hi_handler = CommandHandler('hi', hi)
dm_handler = CommandHandler('send_dm', send_dm)
rules_handler = CommandHandler('rules', rules)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(wee_handler)
dispatcher.add_handler(hoo_handler)
dispatcher.add_handler(hi_handler)
dispatcher.add_handler(dm_handler)
dispatcher.add_handler(rules_handler)

newgame_handler = CommandHandler('newgame', new_game, pass_chat_data=True)
dispatcher.add_handler(newgame_handler)
joingame_handler = CommandHandler('joingame', join_game, pass_chat_data=True,
                                  pass_args=True)
dispatcher.add_handler(joingame_handler)
startgame_handler = CommandHandler('startgame', start_game,
                                   pass_chat_data=True,)
dispatcher.add_handler(startgame_handler)
investigate_handler = CommandHandler('investigate', investigate, 
                                     pass_chat_data=True, pass_args=True)
dispatcher.add_handler(investigate_handler)
endgame_handler = CommandHandler('endgame', end_game, pass_chat_data=True)
dispatcher.add_handler(endgame_handler)