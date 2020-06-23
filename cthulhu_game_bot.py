# -*- coding: utf-8 -*-
"""
Created on Wed Mar 21 14:48:01 2018

@author: Amrita

This program implements a Telegram bot for games of Don't Mess With Cthulhu.

TODO:
    Write more detailed messages in response to commands.
"""

import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging
import cthulhu_game as cg
from telegram.error import Unauthorized
import random


### Helper functions.
def read_message(filepath):
    """
    Returns contents of a text file.
    """
    file = open(filepath, 'r')
    message = file.read()
    file.close()
    return message


def reply_all(update, context, name):
    """
    Send a message from a filepath to the chat.
    """
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=read_message("messages/{}.txt".format(name)))


def send_dm(user_id, context, message):
    """
    Sends a test message directly to the user.
    """
    context.bot.send_message(chat_id=user_id,
                             text=message)


def catch_game_errors(func):
    """
    This is a wrapper function meant to catch all Game Errors.
    """
    def wrapper_game_errors(update, context):
        try:
            initialize_chat_data(update, context)
            initialize_player(update, context)
            func(update, context)
        except cg.GameError as err:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=err.message)
    return wrapper_game_errors


@catch_game_errors
def display_board(update, context):
    """
    Displays the board back to the chat.
    """
    board = context.chat_data["game"].get_board()
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=board)

### Non-game related commands.
def start(update, context):
    """
    Prints out the start/help/rules as requested.
    """
    command = update.message.text.split("@")[0][1:]
    reply_all(update, context, command)


def feedback(update, context):
    """
    Records feedback.
    """
    if len(context.args) > 0:
        feedback = open("ignore/feedback.txt", "a")
        feedback.write("\n" + " ".join(context.args) + "\n")
        feedback.close()
        reply_all(update, context, "feedback_success")
    else:
        reply_all(update, context, "feedback_failure")



### Game-organizational functions.
def new_game(update, context):
    """
    Starts a new game of Don't Mess with Cthulhu in the given chat.
    """
    # Check if a game is already ongoing or pending.
    if "game" in context.chat_data:
        if context.chat_data["game"].game_status == "Unstarted":
            reply_all(update, context, "new_game_pending")
        else:
            reply_all(update, context, "new_game_ongoing")
    # Initialize a game, if there isn't one already.
    initialize_chat_data(update, context)

@catch_game_errors
def join_game(update, context):
    """
    Allows players to join a game of Don't Mess with Cthulhu in the chat.

    TODO: nickname checking.
    """
    context.chat_data["game"].add_player(context.user_data["player"])
    reply_all(update, context, "join_game")


@catch_game_errors
def unjoin_game(update, context):
    """
    Remove a player from a game.
    """
    context.chat_data["game"].remove_player(context.user_data["player"])
    reply_all(update, context, "unjoin")


@catch_game_errors
def spectate(update, context):
    """
    Add a player as a spectator.
    """
    context.chat_data["game"].add_player(context.user_data["player"],
                                         is_playing=False)
    reply_all(update, context, "spectate")



### Helper functions for game-organizational functions.
def initialize_chat_data(update, context):
    """
    Resets chat data to be that of a chat with no pending game.
    TODO: this docstring
    @param chat_data - the chat_data for a given chat.
    """
    if "game" not in context.chat_data:
        context.chat_data["game"] = cg.Game()
        reply_all(update, context, "new_game")
    if "game_settings" not in context.chat_data:
        context.chat_data["game_settings"] = cg.GameSettings()


def initialize_player(update, context):
    """
    If a user doesn't have a player profile associated, make one.
    """
    if "player" not in context.user_data:
        context.user_data["player"] = cg.Player(update.message.from_user.id)
        reply_all(update, context, "new_player")



### Game-running functions.
@catch_game_errors
def start_game(update, context):
    """
    Start the pending game.
    """
    context.chat_data["game"].start_game()
    reply_all(update, context, "start_game")
    send_hand_info(update, context)
    send_role_info(update, context)


def claim(update, context):
    pass


def investigate(update, context):
    pass



### Helper functions for above.
@catch_game_errors
def send_hand_info(update, context):
    """
    DMs every player information about their hand.

    TODO: Handle spectators.
    """
    players = context.chat_data["game"].get_active_players()
    for p in players:
        send_dm(p.p_id, context, p.hand_summary())


@catch_game_errors
def send_role_info(update, context):
    players = context.chat_data["game"].get_active_players()
    for p in players:
        send_dm(p.p_id, context, p.game_data.role)

##########################################################


def pending_players(bot, update, chat_data=None):
    """
    Lists all players for the pending game of Cthulhu.
    """
    message = "List of players: \n"
    if not is_game_ongoing(chat_data) and not is_game_pending(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                     text=read_message("messages/listplayers_failure.txt"))
        return
    for user_id, name in chat_data["pending_players"].items():
        message = message + name + "\n"
    bot.send_message(chat_id=update.message.chat_id, text=message)


def end_game(bot, update, chat_data=None):
    """
    Ends any pending or ongoing game.
    """
    if is_game_ongoing(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=chat_data["game"].get_log())
    reset_chat_data(chat_data)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Any game has been ended. /newgame?")


### Required to set up games.


def is_nickname_valid(name, user_id, chat_data):
    """
    Determines whether a nickname is already used or otherwise invalid.

    @param user_id - the id of the user.
    @param chat_data - the relevant chat data.
    """
    assert "pending_players" in chat_data
    # Check name length.
    if len(name) < 3 or len(name) > 15:
        return False
    # It's okay if the user is already registered under that name.
    if user_id in chat_data["pending_players"]:
        if chat_data["pending_players"][user_id].lower() in name.lower():
            return True
        if name.lower() in chat_data["pending_players"][user_id].lower():
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


### Functions that modify game settings.
def claimsettings(bot, update, chat_data=None, args=None):
    """
    Sets claim settings for this chat.
    """
    if len(args) == 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message('messages/claimsettings_usage.txt'))
    elif "on" in args[0]:
        chat_data["claim_settings"] = True
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message("messages/claimsettings_on.txt"))
    elif "off" in args[0]:
        chat_data["claim_settings"] = False
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

    assert "claim_settings" in chat_data
    # Take in the claim.
    claim = interpret_claim(chat_data["game"], args)
    user_id = update.message.from_user.id
    position = chat_data["game"].get_position(player_id=user_id)
    if not claim:
        bot.send_message(chat_id=update.message.chat_id,
                         text=read_message("messages/invalid_claim.txt"))
        return
    else:
        blank, signs, cthulhu = claim

    if chat_data["claim_settings"]:
        whose_claim = chat_data["game"].get_whose_claim()
        # If claim is valid.
        if position != -1 and (position == whose_claim or whose_claim == -1):
            chat_data["game"].claim(position, blank, signs, cthulhu)
            bot.send_message(chat_id=update.message.chat_id,
                             text=chat_data["game"].display_board())
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text=read_message("messages/claim_not_turn.txt"))
    elif not chat_data["claim_settings"]:
        if position != -1:
            chat_data["game"].claim(position, blank, signs, cthulhu)
            bot.send_message(chat_id=update.message.chat_id,
                             text=chat_data["game"].display_board())
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text=read_message("messages/claim_not_play.txt"))


def blaim(bot, update, chat_data):
    """
    Posts name of player who needs to claim.
    """
    if is_game_ongoing(chat_data):
        pos = chat_data["game"].get_whose_claim()
        if pos < 0:
            bot.send_message(chat_id=update.message.chat_id,
                         text="Anyone can claim!")
            return
        # TODO: tag people.
        name = chat_data["game"].players[pos].get_name()
        bot.send_message(chat_id=update.message.chat_id,
                         text="%s needs to claim." % name)


def blame(bot, update, chat_data):
    """
    Posts name of player who has next move.
    """
    if is_game_ongoing(chat_data):
        pos = chat_data["game"].get_whose_claim()
        if pos < 0:
            pos = chat_data["game"].where_flashlight()
        name = chat_data["game"].players[pos].get_name()
        player_id = chat_data["game"].players[pos].get_id()
        bot.send_message(chat_id=update.message.chat_id,
                         text="[{}](tg://user?id={})".format(name, player_id),
                         parse_mode=telegram.ParseMode.MARKDOWN)


def display(bot, update, chat_data):
    """
    Displays the board.
    """
    if is_game_ongoing(chat_data):
        bot.send_message(chat_id=update.message.chat_id,
                         text=chat_data["game"].display_board())


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
    for user_id in chat_data["spectators"]:
        bot.send_message(chat_id=user_id, text=game.get_log())


def send_hands(bot, game, chat_data):
    """
    Sends hands to players and spectators in the game.
    """
    # Generate and send to players.
    hands = game.get_hands()
    for user_id, hand in hands.items():
        bot.send_message(chat_id=user_id, text=hand)
    # Send info to spectators.
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
    if not is_game_ongoing(chat_data):
        bot.send_message(chat_id=update.message.chat_id, text="No game going!")

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
    name = " ".join(args)
    pos = chat_data["game"].is_valid_name(name)
    if pos == -1:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Invalid input. Try again!")
        return False
    if not chat_data["game"].can_investigate_position(pos):
        bot.send_message(chat_id=update.message.chat_id,
                         text="You cannot investigate this player. Try again!")
        return False
    if chat_data["game"].get_whose_claim() >= 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Claims must first finish!")
        return False
    # Investigate and print result.
    result = chat_data["game"].investigate(pos)
    if "E" in result:
        bot.send_message(chat_id=update.message.chat_id,
                         text="You found an Elder Sign!")
    elif "C" in result:
        bot.send_message(chat_id=update.message.chat_id,
                         text="You found Cthulhu!")
    elif "-" in result:
        bot.send_message(chat_id=update.message.chat_id, text="Nothing...")

    bot.send_message(chat_id=update.message.chat_id,
                     text=chat_data["game"].display_board())
    # Check victory conditions.
    if chat_data["game"].investigators_have_won():
        bot.send_message(chat_id=update.message.chat_id,text="Investigators win!")
        end_game(bot, update, chat_data=chat_data)
        return True
    if chat_data["game"].cultists_have_won():
        bot.send_message(chat_id=update.message.chat_id, text="Cultists win!")
        end_game(bot, update, chat_data=chat_data)
        return True

    if chat_data["game"].redeal():
        bot.send_message(chat_id=update.message.chat_id, text="Round is over!")
        send_hands(bot, chat_data["game"], chat_data)
        bot.send_message(chat_id=update.message.chat_id,
                         text=chat_data["game"].display_board())



### Getting the bot up
# Set up the bot.
# If you want to use this bot yourself, please message me directly.
token = open('ignore/token.txt', 'r').read()
bot = telegram.Bot(token=token)

# Create an updater to fetch updates.
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher

# Log errors for future reference.
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s -'
                    '%(message)s', level=logging.INFO,
                    filename='ignore/logging.txt', filemode='a')


# Command synonyms, where they apply.
start_synonyms = ["start", "help", "rules"]
joingame_synonyms = ["joingame", "join", "addme", "hibitch"]
unjoin_synonyms = ["unjoin", "byebitch", "unspectate"]
investigate_synonyms = ["investigate", "invest", "inv", "dig", "dog", "canine",
                        "do", "vore", "nom"]
claim_synonyms = ["claim", "c"]
blame_synonyms = ["blaim", "blame", "blam"]

# Logistical command handlers.
start_handler = CommandHandler(start_synonyms, start)
feedback_handler = CommandHandler('feedback', feedback)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(feedback_handler)

# Handlers related to organizing a game.
newgame_handler = CommandHandler('newgame', new_game)
joingame_handler = CommandHandler(joingame_synonyms, join_game)
unjoin_handler = CommandHandler(unjoin_synonyms, unjoin_game)
spectate_handler = CommandHandler('spectate', spectate, pass_chat_data=True)
startgame_handler = CommandHandler('startgame', start_game)
dispatcher.add_handler(newgame_handler)
dispatcher.add_handler(joingame_handler)
dispatcher.add_handler(unjoin_handler)
dispatcher.add_handler(spectate_handler)
dispatcher.add_handler(startgame_handler)

pending_handler = CommandHandler('listplayers', pending_players,
                                 pass_chat_data=True)

endgame_handler = CommandHandler('endgame', end_game, pass_chat_data=True)
#dispatcher.add_handler(pending_handler)
#dispatcher.add_handler(endgame_handler)

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

updater.start_polling()
updater.idle()
