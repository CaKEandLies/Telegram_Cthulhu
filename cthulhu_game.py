# -*- coding: utf-8 -*-
"""
Created on Thu Mar 22 11:18:11 2018

@author: Amrita

This module implements classes needed for a game of Cthulhu.

TODO: Implement better errors.
TODO: Implement game settings.
"""
import random
import emojis

class GameError(Exception):
    """
    Exceptions that might occur in the game.
    """
    def __init__(self, message):
        self.message = message


class Card:
    """
    A card for games of Don't Mess with Cthulhu.

    Attributes:
      title - the title of the card.
      description - a description of what the card does.
      symbol - the symbolic representation of the card.
      is_flipped - whether the card has been revealed.
    """

    def __init__(self, ctype=None):
        """
        Initializes a card with default information.

        Arguments:
          type - Optional. If a type of card is specified, will load info.
        """
        self.title = "Null"
        self.description = "A blank card. Should not be in the game."
        self.symbol = "null"
        word_len = len(ctype)
        # Scan for extant data.
        with open("card_information/card_data.txt") as f:
            for line in f:
                if ctype==line[0:word_len]:
                    card_data = line.rstrip().split(",")
                    self.title = card_data[0]
                    self.description = card_data[1]
                    self.symbol = emojis.encode(":{}:".format(card_data[2]))
        self.is_flipped = False

    def __str__(self):
        """
        Returns the symbolic representation of the card.
        """
        if self.is_flipped:
            return self.symbol
        else:
            return emojis.encode(":black_circle:")

    def help(self):
        """
        Returns help on how the card functions.

        TODO
        """
        pass

    def is_flipped(self):
        """
        Returns whether the card is face-up.
        """
        return self.is_flipped

    def flip_up(self):
        """
        Flip the card face-up.
        """
        self.is_flipped = True

    def flip_down(self):
        """
        Flip the card face-down.
        """
        self.is_flipped = False


class PlayerGameData:
    """
    A class containing relevant data for a player in a game of Cthulhu.

    Attributes:
      role - the player's role.
      cards - the cards in the player's hand.
      claim - what the player claims to have.
      has_flashlight - whether the player has the flashlight.
    """
    def __init__(self, role):
        """
        Initialize a player as though they're starting a game.
        """
        self.role = role
        self.cards = []
        self.claim = None
        self.has_flashlight = False


class PlayerStats:
    """
    A class containing statistics about a player's win record.

    Attributes:
    """
    def __init__(self):
        """
        """
        pass


class Player:
    """
    A player for games of Don't Mess with Cthulhu.

    Attributes:
        p_id - the player's ID.
        nickname - the player's current nickname.
        game_status - the status of the player in the game.
        game_data - if the player is in a game, the data associated with it.
        stats - a dictionary containing a lot of player stats.

        role - the player's role in the game.
        has_flashlight - Does the player have the flashlight?
        is_cultist - Is the player a cultist?
        hand - The player's current hand.
        player_id - An id corresponding to this player.
        claim - A tuple representing the player's claim.
    """

    def __init__(self, player_id, nickname=None):
        """
        Initialize a blank Player with a given player id.

        Arguments:
          player_id - the ID to label this Player with.
          nickname - Optional. The player's name.
        """
        self.p_id = player_id
        if nickname:
            self.nickname = nickname
        self.game_status = "Idle"
        self.game_data = None
        self.stats = PlayerStats()

    def __str__(self):
        """
        Returns the players name.
        """
        return self.nickname

    def hand_summary(self):
        """
        Displays a summary of what's in a player's hand.

        Returns:
          contents - a string summarizing hand contents.

        Raises:
          GameError - if no game data exists for the player.
        """
        hand = {}
        contents = ""
        # Ensure this player has a hand.
        if not self.game_data:
            raise GameError("It appears this player isn't in a game.")
        # Count cards in the hand and format them.
        for card in self.game_data.cards:
            if card.title in hand:
                hand[card.title] += 1
            else:
                hand[card.title] = 1
        for card_type in hand:
            contents += "{} {}(s),".format(hand[card_type], card_type)
        return contents

    def display_hand(self, omniscient=False):
        """
        Returns the hand as it should be displayed.

        Arguments:
          omniscient - If True, shows entire contents of hand.
        """
        display = ""
        for card in player.game_data.cards:
            if omniscient:
                display += card.symbol
            else:
                display += str(card)
        return display

    def display_claim(self):
        """
        Displays the player's claim in symbolic form.

        TODO: rewrite this.
        """
        display = ""
        for card in player.game_data.claim:
            pass
        blank, sign, cthulhu = self.claim
        if blank == 0 and sign == 0 and cthulhu == 0:
            return None
        return (blank * "⚪️" + sign * "🔵" + cthulhu * "🔴")

    def set_hand(self, hand):
        """
        Sets the player's hand.

        TODO: rewrite this.

        @param hand - a Hand object representing the player's hand.

        @raises TypeError - if the parameter submitted is not of type Hand.
        """
        if not isinstance(hand, Hand):
            raise TypeError("Argument must be of type Hand.")
        self.hand = hand

    def set_claim(self, blank, elder, cthulhu):
        """
        Set's this person's current claim.

        TODO: Fill this in.
        """
        self.claim = (blank, elder, cthulhu)

    def can_be_investigated(self):
        """
        Returns whether this player can be investigated.
        """
        return (self.hand.can_pick_card() and (not self.has_flashlight))

    def _be_investigated(self):
        """
        Sets has_flashlight to True and returns an unrevealed card from hand.

        This method should only be called by investigate.
        """
        self.has_flashlight = True
        return self.hand.pick_card()

    def investigate(self, player):
        """
        Investigates another player, revealing a card, and reveals the result.

        @raises Exception - if the player does not have the flashlight.
        """
        if not self.has_flashlight:
            raise Exception("Player does not have the flashlight!")
        self.has_flashlight = False
        return player._be_investigated()


class GameSettings:
    """
    Contains game settings that can be passed into a game.

    Attributes:
      expansions - a list of expansions being used.
    """

    def __init__(self):
        """
        Initialize to defaults.
        """
        self.expansions = []


class Game:
    """
    A game of Don't Mess with Cthulhu.

    Attributes:
        players - A list of players in the game or spectating.
        game_status - The status of this game.
        round_counter - Number of rounds that have passed.
        deck - A deck of cards representing the game.
        discard - The discard pile.
        game_settings - The game's settings.
        game_logs - A representation of the game.

        whose_claim - Which player currently needs to claim.
        claim_start - The position of the player that started claims.
    """
    # Role breakdowns for each player count. Note that 1/2 player games
    # do not exist but may be used for testing.
    player_1_roles = ["Investigator"] * 1 + ["Cultist"] * 1
    player_2_roles = ["Investigator"] * 1 + ["Cultist"] * 1
    player_3_roles = ["Investigator"] * 3 + ["Cultist"] * 2
    player_4_roles = ["Investigator"] * 3 + ["Cultist"] * 2
    player_5_roles = ["Investigator"] * 4 + ["Cultist"] * 2
    player_6_roles = ["Investigator"] * 4 + ["Cultist"] * 2
    player_7_roles = ["Investigator"] * 5 + ["Cultist"] * 3
    player_8_roles = ["Investigator"] * 5 + ["Cultist"] * 3
    player_9_roles = ["Investigator"] * 6 + ["Cultist"] * 4
    player_10_roles = ["Investigator"] * 7 + ["Cultist"] * 4
    ROLES = {1: player_1_roles, 2: player_2_roles, 3: player_3_roles,
             4: player_4_roles, 5: player_5_roles, 6: player_6_roles,
             7: player_7_roles, 8: player_8_roles, 9: player_9_roles,
             10: player_10_roles}

    def __init__(self, game_settings=None):
        """
        Start a new, empty game of Don't Mess with Cthulhu.

        Arguments:
          game_id - the game's ID.
        """
        self.players = []
        self.game_status = "Unstarted"

    def add_player(self, player, is_playing=True):
        """
        Add a new player for the game.

        Arguments:
          player - a Player class.
          is_playing - whether the player is playing (True) or spectating.
        """
        # Check that the game accepts new players.
        if self.game_status != "Unstarted" and is_playing:
            raise GameError("The game has already started.")
        # Check that the player hasn't already joined.
        if player in self.players:
            raise GameError("You're already in this game.")
            
        # Add the player as a participant or spectator.
        if is_playing:
            player.game_status = "Playing"
        else:
            player.game_status = "Spectating"
        self.players.append(player)

    def remove_player(self, player):
        """
        Remove a player, if they were playing.
        """
        if player in self.players:
            self.players.remove(player)
        else:
            raise GameError("You weren't in the game.")

    def start_game(self):
        if self.game_status != "Unstarted":
            raise GameError("This game has already been started.")
        else:
            self.game_status = "Ongoing"
            # TODO: things that actually would start this game.

    def get_roles(self):
        """
        Returns a dictionary of player ids and roles.
        """
        roles = {}
        for player in self.players:
            roles[player.get_id()] = player.get_is_cultist()
        return roles

    def get_hands(self):
        """
        Returns a dictionary of player ids and hands.
        """
        hands = {}
        for player in self.players:
            hands[player.get_id()] = player.hand_summary()
        return hands

    def get_formatted_hands(self):
        """
        Returns a formatted string of players hands.
        """
        result = " "
        for player in self.players:
            result += str(player) + ": "
            result += player.display_full_hand() + "\n"
        return result

    def get_log(self):
        """
        Returns a log of the game, which includes hands and roles.
        """
        return self.game_log

    def can_investigate_position(self, position):
        """
        Returns whether the player at position can be investigated.

        @param position - the player's position.
        """
        return self.players[position].can_be_investigated()

    def where_flashlight(self):
        """
        Returns the position of the flashlight.
        """
        return self.flashlight

    def get_whose_claim(self):
        """
        Returns whose claim it is.
        """
        return self.whose_claim

    def investigators_have_won(self):
        """
        Returns whether the investigators have won the game.
        """
        return self.signs_remaining < 1

    def cultists_have_won(self):
        """
        Returns whether cultists have won this round.
        """
        return "C" in self.moves or self.round_number > 4

    def is_valid_name(self, name):
        """
        Returns whether the name is a valid player.

        @name - the player's name.
        """
        for i, player in enumerate(self.players):
            if str(player).lower() in name.lower():
                return i
            elif i > 0 and str(i + 1) in name:
                return i
            elif i == 0 and "1" in name and "10" not in name:
                return i
        return -1

    def get_position(self, player_id=None, name=None):
        """
        Gets the position of a player based on their name or id. Returns -1
        if not found.
        """
        for i, player in enumerate(self.players):
            if player_id == player.get_id():
                return i
            elif name == str(player):
                return i
        return -1

    def deal_cards(self):
        """
        Deals out cards to players and updates game log.
        """
        # Deal out hands.
        hands = self.deck.deal()
        self.game_log += ('\n')
        for i in range(len(self.players)):
            self.players[i].set_hand(hands[i])
            # Update the game log.
            self.game_log += (str(self.players[i]) + ": ")
            self.game_log += self.players[i].display_hand(omniscient=True)
            self.game_log += "\n"
        # Set claims to indicate a new round.
        if self.claims_on:
            self.whose_claim = self.flashlight
            self.claim_start = self.flashlight

    def recollect_cards(self):
        """
        Recollects the cards from a round and resets claims.
        """
        assert len(self.moves) == len(self.players)
        self.deck.return_cards(self.moves)
        self.moves = []
        for player in self.players:
            player.set_claim(0, 0, 0)

    def claim(self, pos, blank, elder, cthulhu):
        """
        Sets the claim for a player at position pos. Do nothing if disallowed.

        @param pos - position of player.
        @param blank - number of blanks to claim.
        @param elder - number of elder signs to claim.
        @param cthulhu - number of cthulhus to claim.
        """
        # If the player can claim, update their claim.
        if self.whose_claim == pos or self.whose_claim == -1:
            self.players[pos].set_claim(blank, elder, cthulhu)
        # If the next person to claim needs to be updated, do so.
        if self.whose_claim == pos:
            self.whose_claim += 1
        # Wrap around the table in terms of claims.
        if self.whose_claim == len(self.players):
            self.whose_claim = 0
        # If everybody has claimed, anyone can now claim.
        if self.whose_claim == self.claim_start:
            self.whose_claim = -1

    def investigate(self, position):
        """
        Investigate the player at position position and return result.
        """
        assert self.can_investigate_position(position)
        # Investigate and add the move to the history.
        temp = self.flashlight
        self.flashlight = position
        move = self.players[temp].investigate(self.players[position])
        self.moves.append(move)
        # If this is the last investigation of a round, update the counter.
        if len(self.moves) == len(self.players):
            self.round_number += 1
        # If an elder sign was found, update the signs remaining.
        if "E" in move:
            self.signs_remaining -= 1
        return move

    def redeal(self):
        """
        If needed, recollect and deal cards. Returns True if done.
        """
        if len(self.moves) >= len(self.players):
            self.recollect_cards()
            self.deal_cards()
            return True
        return False

    def take_move(self):
        """
        Takes a player to investigate via raw_input.

        Obsolete, except for text-based games.
        """
        move = input("Who do you want to investigate? \n")
        for i, player in enumerate(self.players):
            # This will have issues in 10 player games - return to pls.
            if str(i + 1) in move or str(player) in move:
                if player.can_be_investigated():
                    temp = self.flashlight
                    self.flashlight = i
                    return self.players[temp].investigate(player)
                else:
                    print("You can't investigate this player.")
        print("Looks like you entered invalid input. Please try again.")

    def display_board(self):
        """
        Returns a nicely formatted version of the board as it is.
        """
        display = ""
        for i, player in enumerate(self.players):
            display += str(i + 1)
            display += " : "
            display += str(player)
            if self.flashlight == i:
                display += " (🔦) "
            display += " : "
            display += player.display_hand()
            display += "\n"
            if player.display_claim():
                display += ("Claimed: %s" % player.display_claim())
                display += "\n"
            display += "\n"
        display += "Elder Signs remaining: %s" % self.signs_remaining
        return display

    def print_board(self):
        """
        Prints a simple representation of the board.

        Mostly obsolete.
        """
        for i in range(len(self.players)):
            print(str(i + 1), ":", str(self.players[i]),
                  self.players[i].display_hand())
        print("Flashlight is with player", self.flashlight + 1)

    def do_test_round(self):
        """
        Does a simple test round, displaying everything.
        """
        self.deal_cards()
        self.print_board()

        for i, player in enumerate(self.players):
            player.print_info()

        successful_moves = 0
        moves = []
        while (successful_moves < len(self.players)):
            move = self.take_move()
            if move:
                successful_moves += 1
                self.print_board()
                moves.append(move)
            # Maybe split this up into a checker function.
                if "E" in move:
                    self.signs_remaining -= 1
                    if self.signs_remaining == 0:
                        print("Congratulations! Investigator victory!")
                        break
                if "C" in move:
                    print("Cultist victory!")
                    break
        self.recollect_cards(moves)
