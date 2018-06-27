# -*- coding: utf-8 -*-
"""
Created on Wed Mar 21 14:48:01 2018

@author: Amrita

This program implements a Telegram bot for games of Don't Mess With Cthulhu.

TODO:
    Implement a claims system.
    Write more detailed messages in response to commands.
    Write flavortext.
    Potentially implement a spectate command.
    Write a reset state helper function.
    Actually use is_game_pending and is_game_ongoing.
"""

import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging
import cthulhu_game as cg
from telegram.error import Unauthorized
import random


### Generally useful functions.
def read_message(filepath):
    """
    Opens and returns a text file as a string.
    """
    message = open(filepath, 'r').read()
    return message

def is_game_ongoing(chat_data):
    """
    Determines whether a game is ongoing given chat data.
    TODO: use this function.
    """
    if "game_is_ongoing" in chat_data:
        if chat_data["game_is_ongoing"]:
            return True
    return False


def is_game_pending(chat_data):
    """
    Determines whether a game is pending given chat data.
    TODO: use this function.
    """
    if "game_is_pending" in chat_data:
        if chat_data["game_is_pending"]:
            print("is_game_pending is true")
            return True
    print("game isn't pending")
    return False


### Non-game related commands.
def start(bot, update):
    """
    Prints out a message detailing the functionality of this bot.
    """
    bot.send_message(chat_id=update.message.chat_id,
                     text=read_message('messages/start.txt'))


def help_message(bot, update):
    """
    Sends the user a message giving help.
    """
    bot.send_message(chat_id=update.message.chat_id,
                     text=read_message('messages/help.txt'))


def rules(bot, update):
    """
    Sends a message detailing the rules of the game.
    """
    bot.send_message(chat_id=update.message.chat_id,
                     text=read_message('messages/rules.txt'))


def feedback(bot, update, args=None):
    """
    Records feedback.

    TODO: Write this function.
    """
    if len(args) > 0:
        feedback = open("ignore/feedback.txt", "a")
        feedback.write("\n")
        feedback.write(update.message.from_user.first_name)
        feedback.write("\n")
        # Records User ID so that if feature is implemented, can message them
        # about it.
        feedback.write(str(update.message.from_user.id))
        feedback.write("\n")
        feedback.write(" ".join(args))
        feedback.write("\n")
        feedback.close()
        bot.send_message(chat_id=update.message.chat_id,
                         text="Thanks for the feedback!")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Format: /feedback [feedback]")


### Game-organizational functions. 
def new_game(bot, update, chat_data=None):
    """
    Starts a new game of Don't Mess with Cthulhu in the given chat.
    """
    if "game_is_ongoing" not in chat_data:
        chat_data["game_is_ongoing"] = False
        chat_data["game_is_pending"] = True
        chat_data["pending_players"] = {}
        chat_data["spectators"] = []
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/new_game.txt'))
    else:
        if chat_data["game_is_ongoing"]:
            bot.send_message(chat_id=update.message.chat_id,
                             text="There's already a game ongoing. /endgame?")
        elif chat_data["game_is_pending"]:
            bot.send_message(chat_id=update.message.chat_id,
                             text="There's already a game pending. /endgame?")
        else:
            chat_data["pending_players"] = {}
            chat_data["spectators"] = []
            chat_data["game_is_pending"] = True
            chat_data["game_is_ongoing"] = False
            bot.send_message(chat_id=update.message.chat_id,
                             text=read_message('messages/new_game.txt'))


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
                     text="Registered under nickname %s!" % nickname)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Current player count: "
                     "%s" % len(chat_data["pending_players"]))


def unjoin(bot, update, chat_data=None):
    if "game_is_pending" not in chat_data:
        bot.send_message(chat_id=update.message.chat_id,
                         text="No game pending!")
        return
    elif not chat_data["game_is_pending"]:
        bot.send_message(chat_id=update.message.chat_id,
                         text="No game pending!")
        return
    if update.message.from_user.id not in chat_data["pending_players"]:
        bot.send_message(chat_id=update.message.chat_id,
                         text="It's not like you were playing...")
    else:
        del chat_data["pending_players"][update.message.from_user.id]
        bot.send_message(chat_id=update.message.chat_id,
                         text="Succcessfully removed from the game.")


def spectate(bot, update, chat_data=None):
    """
    Signs the user up as a spectator for the current game.
    """
    if not is_game_ongoing(chat_data) and not is_game_pending(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text="There's no game to spectate!")
    elif update.message.from_user.id in chat_data["pending_players"]:
        bot.send_message(chat_id=update.message.chat_id,
                         text="You can't spectate a game you're a player in!")
    else:
        try:
            bot.send_message(chat_id=update.message.from_user.id,
                             text="trying!")
        except Unauthorized as unauth:
            bot.send_message(chat_id=update.message.from_chat,
                             text="You need to start a conversation with me!")
            return
        chat_data["spectators"].append(update.message.from_user.id)
        if is_game_ongoing(chat_data):
            bot.send_message(chat_id=update.message.from_user.id,
                             text=chat_data["game"].get_log())
        bot.send_message(chat_id=update.message.chat_id,
                         text="started!")


def unspectate(bot, update, chat_data=None):
    """
    Removes the user as a spectator.
    """
    if update.message.from_user.id in chat_data["spectators"]:
        chat_data["spectators"].remove(update.message.from_user.id)
        bot.send_message(chat_id=update.message.chat_id,
                         text="stopped spectating!")
        return
    bot.send_message(chat_id=update.message.chat_id,
                     text="You weren't spectating...")


def pending_players(bot, update, chat_data=None):
    """
    Lists all players for the pending game of Cthulhu.
    """
    message = "List of pending players: \n"
    if "game_is_pending" not in chat_data:
        bot.send_message(chat_id=update.message.chat_id,
                         text="No game pending!")
        return
    elif not chat_data["game_is_pending"]:
        bot.send_message(chat_id=update.message.chat_id,
                         text="No game pending!")
        return
    for user_id, name in chat_data["pending_players"].items():
        message = message + name + "\n"
    bot.send_message(chat_id=update.message.chat_id, text=message)


def start_game(bot, update, chat_data=None):
    """
    Starts the pending game.
    """
    # Check that a game with enough players is pending. 
    if "game_is_pending" not in chat_data:
        bot.send_message(chat_id=update.message.chat_id,
                         text="No game pending!")
        return
    if not chat_data["game_is_pending"]:
        bot.send_message(chat_id=update.message.chat_id,
                         text="No game pending!")
        return
    if len(chat_data["pending_players"]) < 4:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Not enough players yet!")
        return
    try:
        for user_id, nickname in chat_data["pending_players"].items():
            bot.send_message(chat_id=user_id, text="Trying to start game!")
    except Unauthorized as unauth:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/start_game_failure.txt'))
        return
    else:
        chat_data["game_is_ongoing"] = True
        chat_data["game_is_pending"] = False
        chat_data["game"] = cg.Game(chat_data["pending_players"])
        begin_game(bot, chat_data["game"], chat_data)
        chat_data["round_number"] = 1
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/start_game.txt'))
        bot.send_message(chat_id=update.message.chat_id,
                         text=chat_data["game"].display_board())
        

def end_game(bot, update, chat_data=None):
    """
    Ends any pending or ongoing game.
    """
    bot.send_message(chat_id=update.message.chat_id,
                     text=chat_data["game"].get_log())
    chat_data["game_is_pending"] = False
    chat_data["game_is_ongoing"] = False
    chat_data["game"] = None
    chat_data["pending_players"] = {}
    chat_data["spectators"] = []
    bot.send_message(chat_id=update.message.chat_id,
                     text=read_message('messages/end_game.txt'))


### Gameplay-related functions.
def claim(bot, update):
    """
    Allows players to declare their claims.

    # TODO: Limit this to the player who can claim.
    # TODO: Write this function.
    """
    keyboard = [InlineKeyboardButton("1", callback_data='1')]
    pass


def send_roles(bot, game, chat_data):
    """
    Sends roles to players in the game.
    """
    roles = game.get_roles()
    spicy = random.randint(0, 100)
    for user_id, is_cultist in roles.items():
        if is_cultist:
            bot.send_message(chat_id=user_id, text="You're a Cultist.")
            if spicy < 5:
                bot.send_message(chat_id=user_id, text="hot take: cum is a soup")
        else:
            bot.send_message(chat_id=user_id, text="You're an Investigator.")
            if spicy < 5:
                bot.send_message(chat_id=user_id, text="are balls ravioli?")
    # Send roles to spectators.
    for user_id in chat_data["spectators"]:
        bot.send_message(chat_id=user_id, text=game.get_log())


def send_hands(bot, game, chat_data):
    """
    Sends hands to players in the game.
    """
    hands = game.get_hands()
    for user_id, hand in hands.items():
        bot.send_message(chat_id=user_id, text=("You have %s blanks, %s signs"
                                                " and %s Cthulhus." % hand))
    for spectator_id in chat_data["spectators"]:
        bot.send_message(chat_id=spectator_id, text=game.get_formatted_hands())


def begin_game(bot, game, chat_data):
    """
    Sends out opening information.
    """
    send_roles(bot, game, chat_data)
    game.deal_cards()
    send_hands(bot, game, chat_data)


def can_investigate(bot, user_id, game):
    """
    Checks whether the user at that id can investigate others.
    """
    return game.get_position(player_id=user_id) == game.where_flashlight()


def investigate(bot, update, chat_data=None, args=None):
    """
    Allows players to investigate others. Returns False on failure.
    # TODO: split this function.
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
        send_hands(bot, chat_data["game"], chat_data)
    bot.send_message(chat_id=update.message.chat_id,
                     text=chat_data["game"].display_board())


### Hidden commands and other miscellany. 
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

def send_dm(bot, update):
    """
    Sends a test message directly to the user.
    """
    bot.send_message(chat_id=update.message.from_user.id,
                     text="sliding into those dungeon masters!")


# Set up the bot.
# If you want to use this bot yourself, please message me directly.
token = open('ignore/token.txt', 'r').read()
bot = telegram.Bot(token=token)

# Create an updater to fetch updates.
updater = Updater(token=token)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s -'
                    '%(message)s', level=logging.INFO,
                    filename='ignore/logging.txt', filemode='a')


# Logistical command handlers.
start_handler = CommandHandler('start', start)
rules_handler = CommandHandler('rules', rules)
help_handler = CommandHandler('help', help_message)
feedback_handler = CommandHandler('feedback', feedback, pass_args=True)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(rules_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(feedback_handler)

# Handlers related to organizing a game.
newgame_handler = CommandHandler('newgame', new_game, pass_chat_data=True)
joingame_handler = CommandHandler('joingame', join_game, pass_chat_data=True,
                                  pass_args=True)
unjoin_handler = CommandHandler('unjoin', unjoin, pass_chat_data=True)
spectate_handler = CommandHandler('spectate', spectate, pass_chat_data=True)
unspectate_handler = CommandHandler('unspectate', unspectate, pass_chat_data=True)
pending_handler = CommandHandler('pendingplayers', pending_players,
                                 pass_chat_data=True)
startgame_handler = CommandHandler('startgame', start_game,
                                   pass_chat_data=True,)
endgame_handler = CommandHandler('endgame', end_game, pass_chat_data=True)
dispatcher.add_handler(newgame_handler)
dispatcher.add_handler(joingame_handler)
dispatcher.add_handler(unjoin_handler)
dispatcher.add_handler(spectate_handler)
dispatcher.add_handler(unspectate_handler)
dispatcher.add_handler(pending_handler)
dispatcher.add_handler(startgame_handler)
dispatcher.add_handler(endgame_handler)

# Handlers for in-game commands.
investigate_handler = CommandHandler('investigate', investigate,
                                     pass_chat_data=True, pass_args=True)
invest_handler = CommandHandler('invest', investigate,
                                pass_chat_data=True, pass_args=True)
dig_handler = CommandHandler('dig', investigate,
                             pass_chat_data=True, pass_args=True)
dispatcher.add_handler(investigate_handler)
dispatcher.add_handler(invest_handler)
dispatcher.add_handler(dig_handler)

# Handlers for "hidden" commands.
wee_handler = CommandHandler('wee', wee)
hoo_handler = CommandHandler('hoo', hoo)
hi_handler = CommandHandler('hi', hi)
dm_handler = CommandHandler('send_dm', send_dm)
dispatcher.add_handler(wee_handler)
dispatcher.add_handler(hoo_handler)
dispatcher.add_handler(hi_handler)
dispatcher.add_handler(dm_handler)
