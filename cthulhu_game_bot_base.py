# -*- coding: utf-8 -*-
"""
Created on Wed Mar 21 14:48:01 2018

@author: Amrita

This program implements a Telegram bot for games of Don't Mess With Cthulhu.

TODO:
    Write more detailed messages in response to commands.
    Write flavortext.
"""

import logging
import cthulhu_game as cg
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
def start(bot, chat_id, **kwargs):
    """
    Prints out a message detailing the functionality of this bot.
    """
    bot.send_message_from_file(chat_id, 'messages/start.txt')


def help_message(bot, chat_id, **kwargs):
    """
    Sends the user a message giving help.
    """
    bot.send_message_from_file(chat_id, 'messages/help.txt')


def rules(bot, chat_id, **kwargs):
    """
    Sends a message detailing the rules of the game.
    """
    bot.send_message_from_file(chat_id, 'messages/rules.txt')


def feedback(bot, chat_id, user_id, user_name, args=None, **kwargs):
    """
    Records feedback.
    """
    if len(args) > 0:
        message = "\n".join([
            "",
            user_name,
            # Records User ID so that if feature is implemented, can message them
            # about it.
            str(user_id),
            " ".join(args),
            "",
        ])
        with open("ignore/feedback.txt", "a") as f:
            f.write(message)

        bot.send_message_from_file(chat_id, 'messages/feedback_success.txt')
    else:
        bot.send_message_from_file(chat_id, 'messages/feedback_failure.txt')


### Game-organizational functions.
def new_game(bot, chat_id, chat_data=None, args=None, **kwargs):
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
                bot.send_message_from_file(chat_id, "messages/new_usage.txt")
                return
        elif len(args) != 0:
            bot.send_message_from_file(chat_id, "messages/new_usage.txt")
            return
        chat_data[GAME_PENDING] = True
        bot.send_message_from_file(chat_id, 'messages/new_game.txt')
    # If a game exists, let players know.
    elif is_game_ongoing(chat_data):
        bot.send_message_from_file(chat_id, 'messages/new_game_ongoing.txt')
    elif is_game_pending(chat_data):
        bot.send_message_from_file(chat_id, 'messages/new_game_pending.txt')
    # This isn't supposed to happen.
    else:
        bot.send_message_from_file(chat_id, "messages/error.txt")


def join_game(bot, chat_data=None, args=None, **kwargs):
    """
    Allows players to join a game of Don't Mess with Cthulhu in the chat.
    """
    chat_id = kwargs['chat_id']
    user_id = kwargs['user_id']
    user_name = kwargs['user_name']
    # Check that a game and space within it exists.
    if not is_game_pending(chat_data):
        bot.send_message_from_file(chat_id, 'messages/join_game_not_pending.txt')
        return
    # Ensure the user isn't already spectating.
    if user_id in chat_data[SPECTATORS]:
        bot.send_message_from_file(chat_id, 'messages/join_game_spectator.txt')
        return
    # Check that the nickname is valid and add the player.
    if args:
        nickname = " ".join(args)
    else:
        nickname = user_name
    if is_nickname_valid(nickname, user_id, chat_data):
        chat_data[PENDING_PLAYERS][user_id] = nickname
        bot.send_message(chat_id, "Joined under nickname %s!" % nickname)
        bot.send_message(chat_id, "Current player count: "
                         "%s" % len(chat_data[PENDING_PLAYERS]))
        if len(chat_data[PENDING_PLAYERS]) == chat_data[MAX_PLAYERS]:
            start_game(bot, chat_data, **kwargs)
    else:
        bot.send_message_from_file(chat_id, "messages/nickname_invalid.txt")


def unjoin(bot, chat_id, user_id, chat_data=None, **kwargs):
    """
    Removes a player from a pending game, if applicable.
    """
    # Check that a game is pending.
    if not is_game_pending(chat_data):
        bot.send_message_from_file(chat_id, 'messages/unjoin_failure.txt')
        return
    # Check that they're playing and remove if so.
    if user_id not in chat_data[PENDING_PLAYERS]:
        bot.send_message_from_file(chat_id, 'messages/unjoin_failure.txt')
    else:
        del chat_data[PENDING_PLAYERS][user_id]
        bot.send_message_from_file(chat_id, 'messages/unjoin.txt')


def spectate(bot, chat_id, user_id, chat_data=None, **kwargs):
    """
    Signs the user up as a spectator for the current game.
    """
    # See if there's a game to spectate.
    if not is_game_ongoing(chat_data) and not is_game_pending(chat_data):
        bot.send_message_from_file(chat_id, "messages/spectate_no_game.txt")
    # Ensure the user isn't already playing.
    elif user_id in chat_data[PENDING_PLAYERS]:
        bot.send_message_from_file(chat_id, "messages/spectate_playing.txt")
    elif user_id in chat_data[SPECTATORS]:
        bot.send_message(chat_id, "You're already spectating!")
    # Add the player as a spectator if allowed, and send the game log so far.
    else:
        try:
            bot.send_message_from_file(user_id, "messages/spectate.txt")
        except Exception as e:
            bot.send_message_from_file(chat_id, "messages/spectate_unauth.txt")
            return
        chat_data[SPECTATORS].append(user_id)
        if is_game_ongoing(chat_data):
            bot.send_message(user_id, chat_data[GAME].get_log())


def unspectate(bot, chat_id, user_id, chat_data=None, **kwargs):
    """
    Removes the user as a spectator, if applicable.
    """
    if SPECTATORS not in chat_data:
        pass
    elif user_id in chat_data[SPECTATORS]:
        chat_data[SPECTATORS].remove(user_id)
        bot.send_message_from_file(user_id, "messages/unspectate.txt")
        return
    bot.send_message_from_file(chat_id, "messages/unspectate_failure.txt")


def pending_players(bot, chat_id, chat_data=None, **kwargs):
    """
    Lists all players for the pending game of Cthulhu.
    """
    if not is_game_ongoing(chat_data) and not is_game_pending(chat_data):
        bot.send_message_from_file(chat_id, "messages/listplayers_failure.txt")
        return

    message_lines = ["List of players: "]
    message_lines.extend(list(chat_data[PENDING_PLAYERS].values()))
    message = "\n".join(message_lines)
    bot.send_message(chat_id, message)


def start_game(bot, chat_id, chat_data=None, **kwargs):
    """
    Starts the pending game.
    """
    # Check that a game with enough players is pending.
    if not is_game_pending(chat_data):
        bot.send_message_from_file(chat_id, 'messages/start_game_dne.txt')
        return
    if len(chat_data[PENDING_PLAYERS]) < chat_data[MIN_PLAYERS]:
        bot.send_message_from_file(chat_id, 'messages/start_game_too_few.txt')
        return
    # Try to message all users.
    try:
        for user_id, nickname in chat_data[PENDING_PLAYERS].items():
            bot.send_message(user_id, "Trying to start game!")
    except Unauthorized as unauth:
        bot.send_message_from_file(chat_id, 'messages/start_game_failure.txt')
        return
    # Start the game!
    else:
        chat_data[GAME_ONGOING] = True
        chat_data[GAME_PENDING] = False
        chat_data[GAME] = cg.Game(chat_data[PENDING_PLAYERS],
                                    claims=chat_data[CLAIM_SETTINGS])
        begin_game(bot, chat_data[GAME], chat_data)
        bot.send_message_from_file(chat_id, 'messages/start_game.txt')
        bot.send_message(chat_id, chat_data[GAME].display_board())


def end_game(bot, chat_id, chat_data=None, **kwargs):
    """
    Ends any pending or ongoing game.
    """
    if is_game_ongoing(chat_data):
        bot.send_message(chat_id, chat_data[GAME].get_log())
    reset_chat_data(chat_data)
    bot.send_message(chat_id, "Any game has been ended. /newgame?")


### Functions that modify game settings.
def claimsettings(bot, chat_id, chat_data=None, args=None, **kwargs):
    """
    Sets claim settings for this chat.
    """
    if len(args) == 0:
        bot.send_message_from_file(chat_id, 'messages/claimsettings_usage.txt')
    elif "on" in args[0]:
        chat_data[CLAIM_SETTINGS] = True
        bot.send_message_from_file(chat_id, "messages/claimsettings_on.txt")
    elif "off" in args[0]:
        chat_data[CLAIM_SETTINGS] = False
        bot.send_message_from_file(chat_id, "messages/claimsettings_off.txt")
    else:
        bot.send_message_from_file(chat_id, 'messages/claimsettings_usage.txt')


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


def claim(bot, chat_id, user_id, chat_data=None, args=None, **kwargs):
    """
    Allows players to declare their claims.
    """
    # Check that a game is going.
    if not is_game_ongoing(chat_data):
        bot.send_message_from_file(chat_id, "messages/claim_no_game.txt")
        return

    assert CLAIM_SETTINGS in chat_data
    # Take in the claim.
    claim = interpret_claim(chat_data[GAME], args)
    position = chat_data[GAME].get_position(player_id=user_id)
    if not claim:
        bot.send_message_from_file(chat_id, "messages/invalid_claim.txt")
        return
    else:
        blank, signs, cthulhu = claim

    if chat_data[CLAIM_SETTINGS]:
        whose_claim = chat_data[GAME].get_whose_claim()
        # If claim is valid.
        if position != -1 and (position == whose_claim or whose_claim == -1):
            chat_data[GAME].claim(position, blank, signs, cthulhu)
            bot.send_message(chat_id, chat_data[GAME].display_board())
        else:
            bot.send_message_from_file(chat_id, "messages/claim_not_turn.txt")
    elif not chat_data[CLAIM_SETTINGS]:
        if position != -1:
            chat_data[GAME].claim(position, blank, signs, cthulhu)
            bot.send_message(chat_id, chat_data[GAME].display_board())
        else:
            bot.send_message_from_file(chat_id, "messages/claim_not_play.txt")


def blaim(bot, chat_id, chat_data, **kwargs):
    """
    Posts name of player who needs to claim.
    """
    if is_game_ongoing(chat_data):
        pos = chat_data[GAME].get_whose_claim()
        if pos < 0:
            bot.send_message(chat_id, "Anyone can claim!")
            return
        # TODO: tag people.
        name = chat_data[GAME].players[pos].get_name()
        bot.send_message(chat_id, "%s needs to claim." % name)


def blame(bot, chat_id, chat_data, **kwargs):
    """
    Posts name of player who has next move.
    """
    if is_game_ongoing(chat_data):
        pos = chat_data[GAME].get_whose_claim()
        if pos < 0:
            pos = chat_data[GAME].where_flashlight()
        name = chat_data[GAME].players[pos].get_name()
        player_id = chat_data[GAME].players[pos].get_id()
        bot.send_message(chat_id, "[{}](tg://user?id={})".format(name, player_id), markdown=True)


def display(bot, chat_id, chat_data, **kwargs):
    """
    Displays the board.
    """
    if is_game_ongoing(chat_data):
        bot.send_message(chat_id, chat_data[GAME].display_board())


def send_roles(bot, game, chat_data):
    """
    Sends roles to players and spectators in the game.
    """
    roles = game.get_roles()
    spicy = random.randint(0, 100)
    for user_id, is_cultist in roles.items():
        if is_cultist:
            bot.send_message(user_id, "You're a Cultist.")
            if spicy < 3:
                bot.send_message_from_file(user_id, "messages/cultist_spam.txt")
        else:
            bot.send_message(user_id, "You're an Investigator.")
            if spicy < 3:
                bot.send_message_from_file(user_id, "messages/investigator_spam.txt")
    # Send roles to spectators.
    for user_id in chat_data[SPECTATORS]:
        bot.send_message(user_id, game.get_log())


def send_hands(bot, game, chat_data):
    """
    Sends hands to players and spectators in the game.
    """
    # Generate and send to players.
    hands = game.get_hands()
    for user_id, hand in hands.items():
        bot.send_message(user_id, "You have %s blanks, %s signs, and %s Cthulhus." % hand)
    # Send info to spectators.
    for spectator_id in chat_data[SPECTATORS]:
        bot.send_message(spectator_id, game.get_formatted_hands())


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


def investigate(bot, chat_id, user_id, chat_data=None, args=None, **kwargs):
    """
    Allows players to investigate others. Returns False on failure.
    # TODO: split this function.
    """
    if not is_game_ongoing(chat_data):
        bot.send_message(chat_id, "No game going!")

    if len(args) < 1:
        bot.send_message(chat_id, "Format: '/investigate name' "
                         " Want to try that again?")
        return False
    if not can_investigate(bot, user_id,
                           chat_data[GAME]):
        bot.send_message(chat_id, "You don't have the flashlight, dummy!")
        return False
    name = " ".join(args)
    pos = chat_data[GAME].is_valid_name(name)
    if pos == -1:
        bot.send_message(chat_id, "Invalid input. Try again!")
        return False
    if not chat_data[GAME].can_investigate_position(pos):
        bot.send_message(chat_id, "You cannot investigate this player. Try again!")
        return False
    if chat_data[GAME].get_whose_claim() >= 0:
        bot.send_message(chat_id, "Claims must first finish!")
        return False
    # Investigate and print result.
    result = chat_data[GAME].investigate(pos)
    if "E" in result:
        bot.send_message(chat_id, "You found an Elder Sign!")
    elif "C" in result:
        bot.send_message(chat_id, "You found Cthulhu!")
    elif "-" in result:
        bot.send_message(chat_id, "Nothing...")

    bot.send_message(chat_id, chat_data[GAME].display_board())
    # Check victory conditions.
    if chat_data[GAME].investigators_have_won():
        bot.send_message(chat_id, "Investigators win!")
        end_game(bot, chat_id, chat_data=chat_data)
        return True
    if chat_data[GAME].cultists_have_won():
        bot.send_message(chat_id, "Cultists win!")
        end_game(bot, chat_id, chat_data=chat_data)
        return True

    if chat_data[GAME].redeal():
        bot.send_message(chat_id, "Round is over!")
        send_hands(bot, chat_data[GAME], chat_data)
        bot.send_message(chat_id, chat_data[GAME].display_board())


### Hidden commands and other miscellany.
def wee(bot, chat_id, **kwargs):
    """
    Replies with a hoo command.
    """
    bot.send_message(chat_id, "/hoo")


def hoo(bot, chat_id, **kwargs):
    """
    Replies with a wee command.
    """
    bot.send_message(chat_id, "/wee")


def hi(bot, chat_id, **kwargs):
    """
    Replies with a hi command.
    """
    bot.send_message(chat_id, "/hi")

def send_dm(bot, user_id, **kwargs):
    """
    Sends a test message directly to the user.
    """
    bot.send_message(user_id, "sliding into those dungeon masters!")


### Bot logic

class BotBase(object):
    """
    Base object for a game-playing bot.  Should be extended by a version that works
    for a communication platform (such as Telegram or Slack).
    """

    def __init__(self, *args, **kwargs):
        # do nothing at this level
        pass

    def send_message(self, chat, text, **kwargs):
        """
        Send a message to a given chat handle (generally a multi-person chat or a DM with one person)
        with the given text.
        """

        raise NotImplementedError("bot needs to be able to send messages")

    def send_message_from_file(self, chat, filename, **kwargs):
        """
        Read message from file, then send it as usual
        """

        return self.send_message(chat, read_message(filename), **kwargs)

    def add_handler(self, fn, *keywords, **kwargs):
        """
        Add a handler to our bot, so that a user providing the given keywords will trigger the given function.

        :param fn:
            The function we want to add as a handler.  Takes one positional argument (this bot object) and a number of
            keyword arguments (often listed in positional form, because Python can do that if the names match):
                - chat_id (the chat group / channel that the keyword was sent via; must be a valid target for the chat
                           argument of send_message)
                - user_id (the user who sent the keyword; must also be a valid target for the chat argument of
                           send_message, which would act as a DM)
                - user_name (the name of the user)
                - chat_data (a dictionary of game data, only passed if pass_chat_data=True; Telegram will send this
                             implicitly, Slack may need it to be manually sent through)
                - args (a list of arguments following the command, only passed if pass_args=True)
        :param keywords:
            The list of keywords which will trigger this handler.
        :param pass_chat_data: whether or not to pass chat_data to the underlying function (default False)
        :param pass_args: whether or not to pass args to the underlying function (default False)
        """

        raise NotImplementedError("bot needs to be able to add handlers")


### Getting the bot up
def add_cthulhu_handlers(bot):
    # Command synonyms, where they apply.
    joingame_synonyms = ["joingame", "join", "addme", "hibitch"]
    unjoin_synonyms = ["unjoin", "byebitch"]
    investigate_synonyms = ["investigate", "invest", "inv", "dig", "dog", "canine",
                            "do", "vore", "nom"]
    claim_synonyms = ["claim", "c"]
    blame_synonyms = ["blaim", "blame", "blam"]

    # Logistical command handlers.
    bot.add_handler(start, "start")
    bot.add_handler(rules, "rules")
    bot.add_handler(help_message, "help")
    bot.add_handler(feedback, "feedback", pass_args=True)

    # Handlers related to organizing a game.
    bot.add_handler(new_game, "newgame", pass_chat_data=True, pass_args=True)
    bot.add_handler(join_game, *joingame_synonyms, pass_chat_data=True, pass_args=True)
    bot.add_handler(unjoin, *unjoin_synonyms, pass_chat_data=True)
    bot.add_handler(spectate, "spectate", pass_chat_data=True)
    bot.add_handler(unspectate, "unspectate", pass_chat_data=True)
    bot.add_handler(pending_players, "listplayers", pass_chat_data=True)
    bot.add_handler(start_game, "startgame", pass_chat_data=True)
    bot.add_handler(end_game, "endgame", pass_chat_data=True)

    # Handlers for in-game commands.
    bot.add_handler(investigate, *investigate_synonyms, pass_chat_data=True, pass_args=True)
    bot.add_handler(claim, *claim_synonyms, pass_chat_data=True, pass_args=True)
    bot.add_handler(blame, *blame_synonyms, pass_chat_data=True, pass_args=True)
    bot.add_handler(display, "display", pass_chat_data=True)

    # Handlers for game settings.
    bot.add_handler(claimsettings, "claimsettings", pass_chat_data=True, pass_args=True)

    # Handlers for "hidden" commands.
    bot.add_handler(wee, "wee")
    bot.add_handler(hoo, "hoo")
    bot.add_handler(hi, "hi")
    bot.add_handler(send_dm, "send_dm")


def add_logging():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s -'
                        '%(message)s', level=logging.INFO,
                        filename='ignore/logging.txt', filemode='a')

