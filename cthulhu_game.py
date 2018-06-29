# -*- coding: utf-8 -*-
"""
Created on Thu Mar 22 11:18:11 2018

@author: Amrita

This module implements classes needed for a game of Cthulhu.

Throughout the module, an Elder Sign is represented as "E", a blank as "-",
and Cthulhu as "C".
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
        claim - A tuple representing the player's claim.
    """

    def __init__(self, name, has_flashlight, is_cultist, player_id=0):
        """
        Initializes an instance of the Player class.
        
        @param name - The player's name.
        @param has_flashlight - Does the player start with it?
        @param is_cultist - Whether the player is a cultist.
        @param player_id - An id corresponding to this player.
        """
        self.name = name
        self.has_flashlight = has_flashlight
        self.is_cultist = is_cultist
        self.hand = Hand([])
        self.id = player_id
        self.claim = (0, 0, 0)

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

    def display_full_hand(self):
        """
        Returns the entire contents of the hand, nicely-formatted.
        
        Unlike display_hand, this displays the entire contents, and unlike
        get_hand, this is nicely-formatted.
        """
        return self.hand.get_full_contents()

    def display_claim(self):
        """
        Displays the player's claim in emoji form.
        """
        blank, sign, cthulhu = self.claim
        if blank == 0 and sign == 0 and cthulhu == 0:
            return None
        return (blank * "⚪️" + sign * "🔵" + cthulhu * "🔴 ")

    def get_id(self):
        """
        Returns the player's id.
        """
        return self.id

    def get_is_cultist(self):
        """
        Returns True if player is a Cultist, False otherwise.
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
   
    def set_claim(self, blank, elder, cthulhu):
        """
        Set's this person's current claim.
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
            # Display only revealed cards.
            if i < self.picked:
                if "-" in card:
                    hand += "⚪️"
                elif "E" in card:
                    hand += "🔵"
                elif "C" in card:
                    hand += "🔴"
            # All unrevealed cards are blank.
            else:
                hand += "⚫"
        return hand
    
    def get_full_contents(self):
        """
        Returns nicely-formatted contents of the entire hand, sorted.
        """
        hand = ""
        hand = hand + self.get_blank() * "⚪️"
        hand = hand + self.get_elder() * "🔵"
        hand = hand + self.get_cthulhu() * "🔴"
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
        if num_players > 10:
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
        game_log - A representation of the game.
        claims_on - Whether claims are enforced.
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

    def __init__(self, players, claims = False):
        """
        Initializes a game of Don't Mess With Cthulhu given player names.

        @param players - A dictionary of player ids: nicknames
        @param claims - Whether claims are strictly enforced

        @raises Exception - if incorrect number of players.
        """
        
        num = len(players)
        if num > 10 or num < 1:
            raise Exception("Incorrect number of players!")
        # Assign roles to players.
        roles = self.ROLES[num]
        random.shuffle(roles)
        starting = random.randint(0, num-1)
        # Set up the game's list of players.
        self.players = []
        position = 0
        for user_id, name in players.items():
            # Initialize a player for each in the list.
            self.players.append(Player(name, position == starting,
                                       "Cultist" in roles[position],
                                       player_id=user_id))
            position += 1
        # Set up a blank gamestate with the flashlight starting at a random
        # player.
        self.flashlight = starting
        self.deck = Deck(num)
        self.signs_remaining = num
        self.moves = []
        self.game_log = "Roles: \n"
        self.round_number = 1
        
        # If claims are enforced, set up who's claim it is. Otherwise, 
        # anyone can claim. 
        self.claims_on = claims
        if self.claims_on:
            self.whose_claim = self.flashlight
            self.claim_start = self.flashlight
        else:
            self.whose_claim = -1
            self.claim_start = -1
        # Log initial roles.
        for i in range(num):
            self.game_log += self.players[i].get_name() + ": " + roles[i]
            self.game_log += "\n"

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
    
    def get_formatted_hands(self):
        """
        Returns a formatted string of players hands.
        """
        result = " "
        for player in self.players:
            result += player.get_name() + ": "
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
        Deals out cards to players and updates game log.
        """
        # Deal out hands.
        hands = self.deck.deal()
        self.game_log += ('\n')
        for i in range(len(self.players)):
            self.players[i].set_hand(hands[i])
            # Update the game log.
            self.game_log += (self.players[i].get_name() + ": ")
            self.game_log += self.players[i].display_full_hand()
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
