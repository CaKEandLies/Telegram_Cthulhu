# -*- coding: utf-8 -*-
"""
Created on Wed Mar 21 14:48:01 2018

@author: Amrita

This program implements a Telegram bot for games of Don't Mess With Cthulhu.

TODO:
    Fix issues wrt valid names. (Done, untested.)
    Print board status at end of round before reshuffle. (Done, untested.)
    Rewrite pending players somewhat. (Done, untested.)
    Enable spectation. (Done, untested.)
    Game prints out log when ended. (Done, untested.)
    Implement a claims system. (Done, untested.)
    Implement a /display command. (Done, untested.)
    Restructure end-of-round information in both investigate functions.
    Write more detailed messages in response to commands.
    Write flavortext.
    Update string formatting to meet newer standards.
"""

import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging
import cthulhu_game as cg
from telegram.error import Unauthorized


### Helper functions.
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


def is_nickname_valid(name, user_id, chat_data):
    """
    Determines whether a nickname is already used or otherwise invalid.
    """
    assert "pending_players" in chat_data
    
    # It's okay if the user is already registered under that name.
    if user_id in chat_data["pending_players"]:
        if chat_data["pending_players"][user_id] == name:
            return True
    # Look for a case-insensitive version of the name in remaining players.
    for user_id, user_name in chat_data["pending_players"].items():
        if name.lower() in user_name.lower():
            return False
        elif user_name.lower() in name.lower():
            return False
    # Check that the name isn't an integer.
    try:
        int(name)
        return False
    except ValueError as e:
        return True


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
    """
    if len(args) > 0:
        feedback = open("ignore/feedback.txt", "a")
        # Records name + User ID so that if feature is implemented, can message
        # them about it.
        feedback.write("\n" + update.message.from_user.first_name + "\n")
        feedback.write(str(update.message.from_user.id))
        feedback.write("\n" + " ".join(args) + "\n" )
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

    # TODO: Ensure in a chat with enough people.
    """
    if not is_game_ongoing(chat_data) and not is_game_pending(chat_data):
        chat_data["game_is_ongoing"] = False
        chat_data["game_is_pending"] = True
        chat_data["pending_players"] = {}
        chat_data["spectators"] = []
        if "claims_settings" not in chat_data:
            chat_data["claim_settings"] = "soft"
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/new_game.txt'))
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="There's already a game here. /endgame?")


def join(bot, update, chat_data=None, args=None):
    """
    Allows players to join a game of Don't Mess with Cthulhu in the chat.
    """
    if not is_game_pending(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text="There appears to be no game pending. /newgame?")
    if len(chat_data["pending_players"]) >= 10:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Game is full, sorry!")
        return

    # Add this player to the list of pending players with a nickname.
    if len(args) > 0:
        nickname = args[0]
    else:
        nickname = update.message.from_user.first_name
    user_id = update.message.from_user.id
    # Check that this username is valid.
    if not is_nickname_valid(nickname, user_id, chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/nickname_failure.txt'))
        return
    # If this was successful, add player and send updates. 
    chat_data["pending_players"][user_id] = nickname
    bot.send_message(chat_id=update.message.chat_id,
                     text="Registered under nickname %s! To change nickname, "
                     "simply use /joingame [nickname] again. " % nickname)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Current player count: "
                     "%s" % len(chat_data["pending_players"]))


def unjoin(bot, update, chat_data=None):
    if not is_game_pending(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/unjoin_failure.txt'))
    elif update.message.from_user.id not in chat_data["pending_players"]:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Like you were playing in the first place...")
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
                             text="Successfully started spectating!")
        except Unauthorized as unauth:
            bot.send_message(chat_id=update.message.from_chat,
                             text="You need to start a conversation with me!")
        else:
            chat_data["spectators"].append(update.message.from_user.id)
            if is_game_ongoing(chat_data):
                bot.send_message(chat_id=update.message.from_user.id,
                                 text=chat_data["game"].get_log())


def unspectate(bot, update, chat_data=None):
    if "spectators" in chat_data:
        if update.from_user.id in chat_data["spectators"]:
            # TODO: delete
            bot.send_message(chat_id=update.message.chat_id,
                             text="stopped spectating!")
            return
    bot.send_message(chat_id=update.message.chat_id,
                     text="you weren't spectating...")


def pending_players(bot, update, chat_data=None):
    """
    Lists all players for the pending game of Cthulhu.
    """
    if not is_game_pending(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text="No game pending!")
        return
    pending_message = "Current list of pending players: \n"
    for user_id, name in chat_data["pending_players"].items():
        pending_message += name
        pending_message += "\n"
    bot.send_message(chat_id=update.message.chat_id, text=pending_message)


def start_game(bot, update, chat_data=None):
    """
    Starts the pending game.
    """
    # Check that a game with enough players is pending. 
    if not is_game_pending(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text="no game to start!")
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
        chat_data["game"] = cg.Game(chat_data["pending_players"],
                                    claim_settings=chat_data["claim_settings"])
        begin_game(bot, chat_data["game"])
        chat_data["round_number"] = 1
        bot.send_message(chat_id=update.message.chat_id,
                         text=chat_data["game"].display_board())


def end_game(bot, update, chat_data=None):
    """
    Ends any pending or ongoing game.
    """
    if "game" in chat_data:
        if chat_data["game"]:
            bot.send_message(chat_id=update.message.chat_id,
                             text=chat_data["game"].get_log())
    chat_data["game_is_pending"] = False
    chat_data["game_is_ongoing"] = False
    chat_data["game"] = None
    chat_data["pending_players"] = {}
    chat_data["spectators"] = []
    bot.send_message(chat_id=update.message.chat_id,
                     text=read_message('messages/end_game.txt'))


### Functions that modify game settings.
def claimsettings(bot, update, chat_data=None, args=None):
    """
    Sets claim settings for this chat.
    """
    # TODO: Flesh this out with user messages. 
    if len(args) == 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text="/claimsettings hard or /claimsettings soft")
    elif "soft" in args[0]:
        chat_data["claim_settings"] = 'soft'
    elif "hard" in args[0]:
        chat_data["claim_settings"] = 'hard'


### Gameplay-related functions.
def interpret_claim(game, args):
    """
    Interprets a user's claim, and returns (-, E, C). Returns False if unknown.

    # TODO: one can technically declare many cthulhus. do i care?
    """
    # TODO: Write a get_round_number function.
    hand_size = 6 - game.round_number
    if len(args) == 1:
        if "C" in arg[0]:
            return (hand_size - 1, 0, 1)
        # Interpret first number as number of elder signs. 
        try:
            signs = int(arg[0])
            assert signs <= hand_size
            return (hand_size - signs, signs, 0)
        except (ValueError, AssertionError) as e:
            return False
    else:
        try:
            signs = int(args[0])
        except ValueError as e:
            return False
        if "C" in args[1]:
            cthulhus = 1
        else:
            try:
                cthulhus = int(args[1])
            except ValueError as e:
                return False
        if signs + cthulhus >= hand_size:
            return False
        else:
            return (hand_size - signs - cthulhus, signs, cthulhus)
        

def claim(bot, update, chat_data=None, args=None):
    """
    Allows players to declare their claims.

    # TODO: Limit this to the player who can claim.
    # TODO: Write this function.
    """
    if not is_game_ongoing(chat_data):
        bot.send_message(chat_id=update.message.chat_id, text="no game!")
        return
    elif "hard" in chat_data["claim_settings"]:
        user_id = update.message.from_user.id
        position = chat_data["game"].get_position(player_id=user_id)
        whose_claim = chat_data['game'].whose_claim()
        if (position != -1 and position == whose_claim) or whose_claim == -1:
            claim = interpret_claim(chat_data["game"], args)
            if claim:
                chat_data["game"].claim(position, claim)
            else:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="invalid input!")
    elif "soft" in chat_data["claim_settings"]:
        claim = interpret_claim(chat_data["game"], args)
        position = chat_data["game"].get_position(player_id=user_id)
        if position != -1:
            chat_data["game"].claim(position, claim)
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="not playing!")


def blaim(bot, update, chat_data):
    """
    Posts name of player who needs to claim.
    """
    if is_game_ongoing(chat_data):
        pos = chat_data["game"].whose_claim()
        if pos < 0:
            bot.send_message(chat_id=update.message.chat_id,
                         text="anyone can claim")
            return
        # TODO: don't do this.
        name = chat_data["game"].players[pos].get_name()
        bot.send_message(chat_id=update.message.chat_id,
                         text="%s needs to claim" % name)


def send_roles(bot, game, chat_data):
    """
    Sends roles to players in the game.
    """
    roles = game.get_roles()
    # Send roles to players.
    for user_id, is_cultist in roles.items():
        if is_cultist:
            bot.send_message(chat_id=user_id, text="You're a Cultist.")
        else:
            bot.send_message(chat_id=user_id, text="You're an Investigator.")
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
            # TODO: Format this more nicely.
            bot.send_message(chat_id=spectator_id, text=str(hand))


def begin_game(bot, game):
    """
    Sends out opening information.
    """
    send_roles(bot, game)
    game.deal_cards()
    send_hands(bot, game)


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
    if not is_game_pending(chat_data):
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

    old_board, result, end_of_round = chat_data["game"].investigate(pos)
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
        bot.send_message(chat_id=update.message.chat_id, text=old_board)
        bot.send_message(chat_id=update.message.chat_id,
                         text="Round is over!")
        chat_data["round_number"] += 1
        if chat_data["round_number"] > 4:
            bot.send_message(chat_id=update.message.chat_id,
                             text="Cultists win by default!")
            bot.end_game(bot, update, chat_data=chat_data)
            return True
        send_hands(bot, chat_data["game"])
    bot.send_message(chat_id=update.message.chat_id,
                     text=chat_data["game"].display_board())


def display(bot, update, chat_data=None):
    if is_game_ongoing(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=chat_data["game"].display_board())
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="no game to display!")


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
                    '%(message)s', level=logging.INFO)


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
joingame_handler = CommandHandler('joingame', join, pass_chat_data=True,
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
dispatcher.add_handler(investigate_handler)

# Handlers for "hidden" commands.
wee_handler = CommandHandler('wee', wee)
hoo_handler = CommandHandler('hoo', hoo)
hi_handler = CommandHandler('hi', hi)
dm_handler = CommandHandler('send_dm', send_dm)
dispatcher.add_handler(wee_handler)
dispatcher.add_handler(hoo_handler)
dispatcher.add_handler(hi_handler)
dispatcher.add_handler(dm_handler)
