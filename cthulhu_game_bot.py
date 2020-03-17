# -*- coding: utf-8 -*-
"""
Created on Wed Mar 21 14:48:01 2018

@author: Amrita

This program implements a Telegram bot for games of Don't Mess With Cthulhu.

TODO:
    Write more detailed messages in response to commands.
    Write flavortext.
"""

import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging
import cthulhu_game as cg
from telegram.error import Unauthorized
import random

### Constants

# keys in chat_data dict
GAME_ONGOING = "game_is_ongoing"
GAME_PENDING = "game_is_pending"
PENDING_PLAYERS = "pending_players"
SPECTATORS = "spectators"
MIN_PLAYERS = "min_players"
MAX_PLAYERS = "max_players"
CLAIM_SETTINGS = "claim_settings"
GAME = "game"


### Generally useful functions.
def read_message(filepath):
    """
    Opens and returns a text file as a string.
    """
    with open(filepath) as f:
        message = f.read()
    return message


def is_game_ongoing(chat_data):
    """
    Determines whether a game is ongoing given chat data.
    
    @param chat_data - the chat_data for a given chat.
    """
    return chat_data.get(GAME_ONGOING, False)


def is_game_pending(chat_data):
    """
    Determines whether a game is pending given chat data.
    
    @param chat_data - the chat_data for a given chat.
    """
    return chat_data.get(GAME_PENDING, False)


def reset_chat_data(chat_data):
    """
    Resets chat data to be that of a chat with no pending game.
    
    @param chat_data - the chat_data for a given chat.
    """
    chat_data[PENDING_PLAYERS] = {}
    chat_data[SPECTATORS] = []
    chat_data[GAME_PENDING] = False
    chat_data[GAME_ONGOING] = False
    chat_data[MIN_PLAYERS] = 3
    chat_data[MAX_PLAYERS] = 10
    if CLAIM_SETTINGS not in chat_data:
        chat_data[CLAIM_SETTINGS] = True


def is_nickname_valid(name, user_id, chat_data):
    """
    Determines whether a nickname is already used or otherwise invalid.

    @param user_id - the id of the user.
    @param chat_data - the relevant chat data.
    """
    assert PENDING_PLAYERS in chat_data
    # Check name length.
    if not (3 <= len(name) <= 15):
        return False

    # check existing usernames
    for other_user_id, other_user_name in chat_data[PENDING_PLAYERS].items():
        # check if the proposed name is a subset of an existing username, or vice versa
        is_subset = name.lower() in other_user_name.lower() or other_user_name.lower() in name.lower()

        # this is guaranteed acceptable if it's you (and you're already registered), and
        # unacceptable if not
        if is_subset:
            return user_id == other_user_id

    # Check that the name isn't an integer.
    if name.isdigit():
        return False

    # we've passed all checks, so it must be fine
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
        message = "\n".join([
            "",
            update.message.from_user.first_name,
            # Records User ID so that if feature is implemented, can message them
            # about it.
            str(update.message.from_user.id),
            " ".join(args),
            "",
        ])
        with open("ignore/feedback.txt", "a") as f:
            f.write(message)

        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message("messages/feedback_success.txt"))
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message("messages/feedback_failure.txt"))


### Game-organizational functions. 
def new_game(bot, update, chat_data=None, args=None):
    """
    Starts a new game of Don't Mess with Cthulhu in the given chat.
    """
    # If no game exists, start one.
    if not is_game_ongoing(chat_data) and not is_game_pending(chat_data):
        reset_chat_data(chat_data)
        # Set minimum and maximum players
        if len(args) == 2:
            try:
                min_players = int(args[0])
                max_players = int(args[1])
                assert min_players <= max_players
                assert min_players >= 3
                assert max_players <= 10
                chat_data[MIN_PLAYERS] = min_players
                chat_data[MAX_PLAYERS] = max_players
            except (ValueError, AssertionError) as e:
                bot.send_message(chat_id=update.message.chat_id,
                                 text=read_message("messages/new_usage.txt"))
                return
        elif len(args) != 0:
            bot.send_message(chat_id=update.message.chat_id,
                                 text=read_message("messages/new_usage.txt"))
            return
        chat_data[GAME_PENDING] = True
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/new_game.txt'))
    # If a game exists, let players know.
    elif is_game_ongoing(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/new_game_ongoing.txt'))
    elif is_game_pending(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/new_game_pending.txt'))
    # This isn't supposed to happen.
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message("messages/error.txt"))


def join_game(bot, update, chat_data=None, args=None):
    """
    Allows players to join a game of Don't Mess with Cthulhu in the chat.
    """
    # Check that a game and space within it exists.
    if not is_game_pending(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/join_game_not_pending.txt'))
        return
    # Ensure the user isn't already spectating.
    user_id = update.message.from_user.id
    if user_id in chat_data[SPECTATORS]:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/join_game_spectator.txt'))
        return
    # Check that the nickname is valid and add the player.
    if args:
        nickname = " ".join(args)
    else:
        nickname = update.message.from_user.first_name
    if is_nickname_valid(nickname, user_id, chat_data):
        chat_data[PENDING_PLAYERS][user_id] = nickname
        bot.send_message(chat_id=update.message.chat_id,
                         text="Joined under nickname %s!" % nickname)
        bot.send_message(chat_id=update.message.chat_id,
                         text="Current player count: "
                         "%s" % len(chat_data[PENDING_PLAYERS]))
        if len(chat_data[PENDING_PLAYERS]) == chat_data[MAX_PLAYERS]:
            start_game(bot, update, chat_data)
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message("messages/nickname_invalid.txt"))


def unjoin(bot, update, chat_data=None):
    """
    Removes a player from a pending game, if applicable.
    """
    # Check that a game is pending.
    if not is_game_pending(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/unjoin_failure.txt'))
        return
    # Check that they're playing and remove if so.
    if update.message.from_user.id not in chat_data[PENDING_PLAYERS]:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/unjoin_failure.txt'))
    else:
        del chat_data[PENDING_PLAYERS][update.message.from_user.id]
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/unjoin.txt'))


def spectate(bot, update, chat_data=None):
    """
    Signs the user up as a spectator for the current game.
    """
    # See if there's a game to spectate.
    if not is_game_ongoing(chat_data) and not is_game_pending(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message("messages/spectate_no_game.txt"))
    # Ensure the user isn't already playing.
    elif update.message.from_user.id in chat_data[PENDING_PLAYERS]:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message("messages/spectate_playing.txt"))
    elif update.message.from_user.id in chat_data[SPECTATORS]:
        bot.send_message(chat_id=update.message.chat_id,
                         text="You're already spectating!")
    # Add the player as a spectator if allowed, and send the game log so far.
    else:
        try:
            bot.send_message(chat_id=update.message.from_user.id,
                             text=read_message("messages/spectate.txt"))
        except Unauthorized as unauth:
            bot.send_message(chat_id=update.message.from_chat,
                             text=read_message("messages/spectate_unauth.txt"))
            return
        chat_data[SPECTATORS].append(update.message.from_user.id)
        if is_game_ongoing(chat_data):
            bot.send_message(chat_id=update.message.from_user.id,
                             text=chat_data[GAME].get_log())


def unspectate(bot, update, chat_data=None):
    """
    Removes the user as a spectator, if applicable.
    """
    if SPECTATORS not in chat_data:
        pass
    elif update.message.from_user.id in chat_data[SPECTATORS]:
        chat_data[SPECTATORS].remove(update.message.from_user.id)
        bot.send_message(chat_id=update.message.from_user.id,
                         text=read_message("messages/unspectate.txt"))
        return
    bot.send_message(chat_id=update.message.chat_id,
                     text=read_message("messages/unspectate_failure.txt"))


def pending_players(bot, update, chat_data=None):
    """
    Lists all players for the pending game of Cthulhu.
    """
    if not is_game_ongoing(chat_data) and not is_game_pending(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                     text=read_message("messages/listplayers_failure.txt"))
        return

    message_lines = ["List of players: "]
    message_lines.extend(list(chat_data[PENDING_PLAYERS].values()))
    message = "\n".join(message_lines)
    bot.send_message(chat_id=update.message.chat_id, text=message)


def start_game(bot, update, chat_data=None):
    """
    Starts the pending game.
    """
    # Check that a game with enough players is pending. 
    if not is_game_pending(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/start_game_dne.txt'))
        return
    if len(chat_data[PENDING_PLAYERS]) < chat_data[MIN_PLAYERS]:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/start_game_too_few.txt'))
        return
    # Try to message all users.
    try:
        for user_id, nickname in chat_data[PENDING_PLAYERS].items():
            bot.send_message(chat_id=user_id, text="Trying to start game!")
    except Unauthorized as unauth:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/start_game_failure.txt'))
        return
    # Start the game!
    else:
        chat_data[GAME_ONGOING] = True
        chat_data[GAME_PENDING] = False
        chat_data[GAME] = cg.Game(chat_data[PENDING_PLAYERS],
                                    claims=chat_data[CLAIM_SETTINGS])
        begin_game(bot, chat_data[GAME], chat_data)
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/start_game.txt'))
        bot.send_message(chat_id=update.message.chat_id,
                         text=chat_data[GAME].display_board())
        

def end_game(bot, update, chat_data=None):
    """
    Ends any pending or ongoing game.
    """
    if is_game_ongoing(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=chat_data[GAME].get_log())
    reset_chat_data(chat_data)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Any game has been ended. /newgame?")


### Functions that modify game settings.
def claimsettings(bot, update, chat_data=None, args=None):
    """
    Sets claim settings for this chat.
    """
    if len(args) == 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/claimsettings_usage.txt'))
    elif "on" in args[0]:
        chat_data[CLAIM_SETTINGS] = True
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message("messages/claimsettings_on.txt"))
    elif "off" in args[0]:
        chat_data[CLAIM_SETTINGS] = False
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message("messages/claimsettings_off.txt"))
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/claimsettings_usage.txt'))


### Gameplay-related functions.
def interpret_claim(game, args):
    """
    Interprets a user's claim, and returns (-, E, C). Returns False if unknown.
    """
    hand_size = 6 - game.round_number
    # Interpret single-argument claims.
    if len(args) == 0:
        return False
    elif len(args) == 1:
        # See if the first argument is a cthulhu claim.
        if "rocks" in args[0].lower():
            return (hand_size, 0, 0)
        elif "c" in args[0].lower():
            return (hand_size - 1, 0, 1)
        # Interpret first number as number of elder signs.
        try:
            signs = int(args[0])
            assert signs <= hand_size
            return (hand_size - signs, signs, 0)
        except (ValueError, AssertionError) as e:
            return False
    # Interpret double-argument claims.
    elif len(args) > 1:
        # The first argument must be a number.
        try:
            signs = int(args[0])
        except ValueError as e:
            return False
        # The second can be either C or a number.
        if "c" in args[1].lower():
            cthulhus = 1
        else:
            try:
                cthulhus = int(args[1])
            except ValueError as e:
                return False
        # Check the claim fits in a hand size.
        if signs + cthulhus > hand_size:
            return False
        else:
            return (hand_size - signs - cthulhus, signs, cthulhus)

def claim(bot, update, chat_data=None, args=None):
    """
    Allows players to declare their claims.
    """
    # Check that a game is going.
    if not is_game_ongoing(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message("messages/claim_no_game.txt"))
        return

    assert CLAIM_SETTINGS in chat_data
    # Take in the claim.
    claim = interpret_claim(chat_data[GAME], args)
    user_id = update.message.from_user.id
    position = chat_data[GAME].get_position(player_id=user_id)
    if not claim:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message("messages/invalid_claim.txt"))
        return
    else:
        blank, signs, cthulhu = claim

    if chat_data[CLAIM_SETTINGS]:
        whose_claim = chat_data[GAME].get_whose_claim()
        # If claim is valid.
        if position != -1 and (position == whose_claim or whose_claim == -1):
            chat_data[GAME].claim(position, blank, signs, cthulhu)
            bot.send_message(chat_id=update.message.chat_id,
                             text=chat_data[GAME].display_board())
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text=read_message("messages/claim_not_turn.txt"))
    elif not chat_data[CLAIM_SETTINGS]:
        if position != -1:
            chat_data[GAME].claim(position, blank, signs, cthulhu)
            bot.send_message(chat_id=update.message.chat_id,
                             text=chat_data[GAME].display_board())
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text=read_message("messages/claim_not_play.txt"))


def blaim(bot, update, chat_data):
    """
    Posts name of player who needs to claim.
    """
    if is_game_ongoing(chat_data):
        pos = chat_data[GAME].get_whose_claim()
        if pos < 0:
            bot.send_message(chat_id=update.message.chat_id,
                         text="Anyone can claim!")
            return
        # TODO: tag people.
        name = chat_data[GAME].players[pos].get_name()
        bot.send_message(chat_id=update.message.chat_id,
                         text="%s needs to claim." % name)


def blame(bot, update, chat_data):
    """
    Posts name of player who has next move.
    """
    if is_game_ongoing(chat_data):
        pos = chat_data[GAME].get_whose_claim()
        if pos < 0:
            pos = chat_data[GAME].where_flashlight()
        name = chat_data[GAME].players[pos].get_name()
        player_id = chat_data[GAME].players[pos].get_id()
        bot.send_message(chat_id=update.message.chat_id,
                         text="[{}](tg://user?id={})".format(name, player_id),
                         parse_mode=telegram.ParseMode.MARKDOWN)


def display(bot, update, chat_data):
    """
    Displays the board.
    """
    if is_game_ongoing(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=chat_data[GAME].display_board())


def send_roles(bot, game, chat_data):
    """
    Sends roles to players and spectators in the game.
    """
    roles = game.get_roles()
    spicy = random.randint(0, 100)
    for user_id, is_cultist in roles.items():
        if is_cultist:
            bot.send_message(chat_id=user_id, text="You're a Cultist.")
            if spicy < 3:
                bot.send_message(chat_id=user_id,
                                 text=read_message("messages/cultist_spam.txt"))
        else:
            bot.send_message(chat_id=user_id, text="You're an Investigator.")
            if spicy < 3:
                bot.send_message(chat_id=user_id,
                                 text=read_message("messages/investigator_spam.txt"))
    # Send roles to spectators.
    for user_id in chat_data[SPECTATORS]:
        bot.send_message(chat_id=user_id, text=game.get_log())


def send_hands(bot, game, chat_data):
    """
    Sends hands to players and spectators in the game.
    """
    # Generate and send to players.
    hands = game.get_hands()
    for user_id, hand in hands.items():
        bot.send_message(chat_id=user_id, text=("You have %s blanks, %s signs"
                                                " and %s Cthulhus." % hand))
    # Send info to spectators.
    for spectator_id in chat_data[SPECTATORS]:
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
    if not is_game_ongoing(chat_data):
        bot.send_message(chat_id=update.message.chat_id, text="No game going!")

    if len(args) < 1:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Format: '/investigate name' "
                         " Want to try that again?")
        return False
    if not can_investigate(bot, update.message.from_user.id,
                           chat_data[GAME]):
        bot.send_message(chat_id=update.message.chat_id,
                         text="You don't have the flashlight, dummy!")
        return False
    name = " ".join(args)
    pos = chat_data[GAME].is_valid_name(name)
    if pos == -1:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Invalid input. Try again!")
        return False
    if not chat_data[GAME].can_investigate_position(pos):
        bot.send_message(chat_id=update.message.chat_id,
                         text="You cannot investigate this player. Try again!")
        return False
    if chat_data[GAME].get_whose_claim() >= 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Claims must first finish!")
        return False
    # Investigate and print result.
    result = chat_data[GAME].investigate(pos)
    if "E" in result:
        bot.send_message(chat_id=update.message.chat_id,
                         text="You found an Elder Sign!")
    elif "C" in result:
        bot.send_message(chat_id=update.message.chat_id,
                         text="You found Cthulhu!")
    elif "-" in result:
        bot.send_message(chat_id=update.message.chat_id, text="Nothing...")
    
    bot.send_message(chat_id=update.message.chat_id, 
                     text=chat_data[GAME].display_board())
    # Check victory conditions.
    if chat_data[GAME].investigators_have_won():
        bot.send_message(chat_id=update.message.chat_id,text="Investigators win!")
        end_game(bot, update, chat_data=chat_data)
        return True
    if chat_data[GAME].cultists_have_won():
        bot.send_message(chat_id=update.message.chat_id, text="Cultists win!")
        end_game(bot, update, chat_data=chat_data)
        return True
    
    if chat_data[GAME].redeal():
        bot.send_message(chat_id=update.message.chat_id, text="Round is over!")
        send_hands(bot, chat_data[GAME], chat_data)
        bot.send_message(chat_id=update.message.chat_id,
                         text=chat_data[GAME].display_board())


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


### Getting the bot up
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


# Command synonyms, where they apply.
joingame_synonyms = ["joingame", "join", "addme", "hibitch"]
unjoin_synonyms = ["unjoin", "byebitch"]
investigate_synonyms = ["investigate", "invest", "inv", "dig", "dog", "canine",
                        "do", "vore", "nom"]
claim_synonyms = ["claim", "c"]
blame_synonyms = ["blaim", "blame", "blam"]

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
newgame_handler = CommandHandler('newgame', new_game, pass_chat_data=True,
                                 pass_args=True)
joingame_handler = CommandHandler(joingame_synonyms, join_game, 
                                  pass_chat_data=True, pass_args=True)
unjoin_handler = CommandHandler(unjoin_synonyms, unjoin, pass_chat_data=True)
spectate_handler = CommandHandler('spectate', spectate, pass_chat_data=True)
unspectate_handler = CommandHandler('unspectate', unspectate, pass_chat_data=True)
pending_handler = CommandHandler('listplayers', pending_players,
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
investigate_handler = CommandHandler(investigate_synonyms, investigate,
                                     pass_chat_data=True, pass_args=True)
claim_handler = CommandHandler(claim_synonyms, claim, pass_chat_data=True,
                               pass_args=True)
blaim_handler = CommandHandler(blame_synonyms, blame, pass_chat_data=True)
display_handler = CommandHandler("display", display, pass_chat_data=True)
dispatcher.add_handler(investigate_handler)
dispatcher.add_handler(claim_handler)
dispatcher.add_handler(blaim_handler)
dispatcher.add_handler(display_handler)

# Handlers for game settings.
claimsettings_handler = CommandHandler('claimsettings', claimsettings,
                                     pass_chat_data=True, pass_args=True)
dispatcher.add_handler(claimsettings_handler)

# Handlers for "hidden" commands.
wee_handler = CommandHandler('wee', wee)
hoo_handler = CommandHandler('hoo', hoo)
hi_handler = CommandHandler('hi', hi)
dm_handler = CommandHandler('send_dm', send_dm)
dispatcher.add_handler(wee_handler)
dispatcher.add_handler(hoo_handler)
dispatcher.add_handler(hi_handler)
dispatcher.add_handler(dm_handler)
