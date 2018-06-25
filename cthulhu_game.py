# -*- coding: utf-8 -*-
"""
Created on Thu Mar 22 11:18:11 2018

@author: Amrita

This module implements classes needed for a game of Cthulhu.

Throughout the module, an Elder Sign is represented as "E", a blank as "-",
and Cthulhu as "C".

TODO:
    Implement a claims system.
    Fix the is_valid_name function.
"""
import random


class Player:
    """
    A player for games of Don't Mess with Cthulhu.

    Attributes:
        name - A player name.
        has_flashlight - Does the player have the flashlight?
        is_cultist - Is the player a cultist?
        hand - The player's current hand.
        player_id - An id corresponding to this player.

    # TODO: Implement a way to track whether this player can claim.
    """

    def __init__(self, name, has_flashlight, is_cultist, player_id=0):
        """
        Initializes an instance of the Player class.
        """
        self.name = name
        self.has_flashlight = has_flashlight
        self.is_cultist = is_cultist
        self.hand = Hand([])
        self.id = player_id

    def __str__(self):
        """
        Returns the players name.
        """
        return self.name

    def get_name(self):
        """
        Returns the players' name.
        """
        return self.name

    def get_hand(self):
        """
        Returns the contents of the players' hands as a tuple of (-, E, C).

        Unlike display_hand, this returns an omniscient summary of what's in
        the player's hand.
        """
        return (self.hand.get_blank(), self.hand.get_elder(),
                self.hand.get_cthulhu())

    def display_hand(self):
        """
        Returns the hand as it should be displayed.

        Unlike get_hand, this accounts for which cards have already been
        revealed.
        """
        return self.hand.get_contents()

    def get_id(self):
        """
        Returns the player's id.
        """
        return self.id

    def get_is_cultist(self):
        """
        Returns True if player is a Cultist.
        """
        return self.is_cultist

    def set_hand(self, hand):
        """
        Sets the player's hand.

        @param hand - a Hand object representing the player's hand.

        @raises TypeError - if the parameter submitted is not of type Hand.
        """
        if not isinstance(hand, Hand):
            raise TypeError("Argument must be of type Hand.")
        self.hand = hand

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

        #TODO: Raise exception if player does not have flashlight.
        """
        self.has_flashlight = False
        return player._be_investigated()


class Hand:
    """
    Contains information about one's hand.

    Attributes:
        elder - Number of elder signs.
        blank - Number of blanks.
        cthulhu - Number of cthulhus.
        picked - Number of times this hand has been picked in this round.
    """

    def __init__(self, contents):
        """
        Initializes a hand given a list of contents.

        @param contents - a list with comma-separated contents.

        @raises ValueError - if unknown element.
        """
        self.blank = 0
        self.elder = 0
        self.cthulhu = 0
        for element in contents:
            if "-" in element:
                self.blank += 1
            elif "E" in element:
                self.elder += 1
            elif "C" in element:
                self.cthulhu += 1
            else:
                raise ValueError("Unrecognized card!")
        # Shuffle contents of hand.
        self.picked = 0
        self.contents = []
        for element in contents:
            self.contents.append(element)
        random.shuffle(self.contents)

    def get_blank(self):
        """
        Returns the number of blank cards in the hand.
        """
        return self.blank

    def get_elder(self):
        """
        Returns the number of elder signs in the hand.
        """
        return self.elder

    def get_cthulhu(self):
        """
        Returns the number of cthulhus in the hand.
        """
        return self.cthulhu

    def can_pick_card(self):
        """
        Returns whether a card can be picked.
        """
        return self.picked < len(self.contents)

    def get_contents(self):
        """
        Returns nicely-formatted contents of the hand, keeping in mind reveals.
        """
        hand = ""
        for i, card in enumerate(self.contents):
            if i < self.picked:
                if "-" in card:
                    hand += "⚪️"
                elif "E" in card:
                    hand += "🔵"
                elif "C" in card:
                    hand += "🔴"
            else:
                hand += "⚫"
        return hand

    def pick_card(self):
        """
        Picks a card from this hand and returns the value.

        @return - Returns a string containing the contents of the card.

        @raises - AssertionError if the hand has already been picked through.
        """
        if self.picked > len(self.contents):
            raise Exception("You can't pick a card from this hand!")
        self.picked += 1
        return self.contents[self.picked - 1]


class Deck:
    """
    A deck containing all Cthulhu cards currently in play.

    Attributes:
        cthulhus - the number of cthulu cards in the deck.
        signs - the number of elder signs in the deck.
        blanks - the number of blank cards in the deck.
        round_count - how many rounds have previously been played.
    """

    def __init__(self, num_players):
        """
        initializes  deck for the given number of players.

        @raises AssertionError - if number of players isn't 4-10.
        """
        self.round_count = 0
        self.signs = num_players
        if num_players > 10 or num_players < 4:
            raise Exception("Incorrect number of players!")
        if (num_players > 8):
            self.cthulhus = 2
        else:
            self.cthulhus = 1
        self.blanks = (5*num_players) - self.signs - self.cthulhus
        self.num_players = num_players

    def deal(self):
        """
        Deals out cards from the deck.

        @return - Returns a list of Hands.
        """
        num_cards = 5 - self.round_count
        n_players = self.num_players

        deck = ["-"] * self.blanks + ["E"] * self.signs + ["C"] * self.cthulhus
        random.shuffle(deck)
        hands = []
        for i in range(n_players):
            hands.append(Hand(deck[i * num_cards: (i+1) * num_cards]))

        self.round_count += 1
        return hands

    def return_cards(self, removed):
        """
        Updates the deck based on which cards were revealed this turn.

        @raise Warning - if incorrect number of cards removed
        @raise Exception - if unrecognized card.
        """
        if not len(removed) == self.num_players:
            raise Warning("Incorrect number of cards removed!")
        for card in removed:
            if "-" in card:
                self.blanks -= 1
            elif "E" in card:
                self.signs -= 1
            elif "C" in card:
                self.cthulhus -= 1
            else:
                raise Exception("Unrecognized card!")


class Game:
    """
    A game of Don't Mess with Cthulhu.

    Attributes:
        players - A list of players in the game.
        round_counter - Number of rounds that have passed.
        deck - A deck of cards representing the game.
        signs_remaining - Number of Elder Signs remaining.
        flashlight - The index of the player who has the flashlight.

    TODO:
        Fix off-by-one errors, potentially.
        Implement a system for claiming.
    """
    player_4_roles = ["Investigator"] * 3 + ["Cultist"] * 2
    player_5_roles = ["Investigator"] * 4 + ["Cultist"] * 2
    player_6_roles = ["Investigator"] * 4 + ["Cultist"] * 2
    player_7_roles = ["Investigator"] * 5 + ["Cultist"] * 3
    player_8_roles = ["Investigator"] * 5 + ["Cultist"] * 3
    player_9_roles = ["Investigator"] * 6 + ["Cultist"] * 4
    player_10_roles = ["Investigator"] * 7 + ["Cultist"] * 4
    ROLES = {4: player_4_roles, 5: player_5_roles, 6: player_6_roles,
             7: player_7_roles, 8: player_8_roles, 9: player_9_roles,
             10: player_10_roles}

    def __init__(self, players, game_id=0):
        """
        Initializes a game of Don't Mess With Cthulhu given player names.

        @param players - A dictionary of player ids: nicknames

        @raises Exception - if incorrect number of players.
        """
        num = len(players)
        if num > 10 or num < 4:
            raise Exception("Incorrect number of players!")

        roles = self.ROLES[num]
        random.shuffle(roles)
        starting = random.randint(0, num-1)

        self.players = []
        position = 0
        for user_id, name in players.items():
            # Initialize a player for each in the list.
            self.players.append(Player(name, position == starting,
                                       "Cultist" in roles[position],
                                       player_id=user_id))
            position += 1

        self.flashlight = starting
        self.deck = Deck(num)
        self.signs_remaining = num
        self.game_id = game_id
        self.moves = []

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
            hands[player.get_id()] = player.get_hand()
        return hands

    def can_investigate_position(self, position):
        """
        Returns whether the player at position can be investigated.
        """
        return self.players[position].can_be_investigated()

    def where_flashlight(self):
        """
        Returns the position of the flashlight.
        """
        return self.flashlight

    def investigators_have_won(self):
        """
        Returns whether the investigators have won the game.
        """
        return self.signs_remaining < 1

    def cultists_have_won(self):
        """
        Returns whether cultists have won this round.
        """
        return "C" in self.moves

    def is_valid_name(self, name):
        """
        Returns whether the name is a valid player.
        """
        for i, player in enumerate(self.players):
            if player.get_name().lower() in name.lower():
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
            elif name == player.get_name():
                return i
        return -1

    def deal_cards(self):
        """
        Deals out cards to players.
        """
        hands = self.deck.deal()
        for i in range(len(self.players)):
            self.players[i].set_hand(hands[i])

    def recollect_cards(self):
        """
        Recollects the cards from a round.
        """
        assert len(self.moves) == len(self.players)
        self.deck.return_cards(self.moves)
        self.moves = []

    def investigate(self, position):
        """
        Investigate the player at position position.
        """
        assert self.can_investigate_position(position)
        temp = self.flashlight
        self.flashlight = position
        move = self.players[temp].investigate(self.players[position])
        self.moves.append(move)
        end_of_round = False
        if "E" in move:
            self.signs_remaining -= 1
        if len(self.moves) >= len(self.players):
            print(self.moves)
            self.recollect_cards()
            self.deal_cards()
            end_of_round = True
        return move, end_of_round

    def take_move(self):
        """
        Takes a player to investigate via raw_input.

        # Obsolete, except for text-based games.
        """
        move = input("Who do you want to investigate? \n")
        for i, player in enumerate(self.players):
            # This will have issues in 10 player games - return to pls.
            if str(i + 1) in move or player.get_name() in move:
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
            display += player.get_name()
            if self.flashlight == i:
                display += " (🔦) "
            display += " : "
            display += player.display_hand()
            display += "\n"
        display += "Elder Signs remaining: %s" % self.signs_remaining
        return display

    def print_board(self):
        """
        Prints a simple representation of the board.
        """
        for i in range(len(self.players)):
            print(str(i + 1), ":", self.players[i].get_name(),
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
