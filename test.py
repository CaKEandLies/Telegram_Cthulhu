# -*- coding: utf-8 -*-
"""
Created on Tue Mar 20 17:16:28 2018

@author: Amrita
"""

import random


class Deck:
    """
    Represents a Cthulu deck. 
    """
    def __init__(self, players):
        """
        Initializes a deck of cards, given a player list.
        
        @players - a list of players.
        """
        self.num_players = len(players)
        self.players = players
        self.num_signs = len(players)
        if len(players) > 8:
            self.num_cthulhu = 2
        else:
            self.num_cthulhu = 1
        self.num_blank = 5*len(players) - self.num_cthulhu - self.num_signs
        self.create_deck()

    def create_deck(self):
        """
        Creates a Cthulhu deck of cards, represented as a list.
        """
        self.deck = []
        for i in range(self.num_blank):
            self.deck.append("-")
        for i in range(self.num_cthulhu):
            self.deck.append("C")
        for i in range(self.num_signs):
            self.deck.append("E")
        random.shuffle(self.deck)

    def deal_cards(self):
        """
        Deals cards out to players from the current deck and prints results.
        """
        hand_size = int(len(self.deck)/self.num_players)
        for i in range(self.num_players):
            start = i * hand_size
            end = (i + 1) * (hand_size)
            to_print = ""
            for card in self.deck[start:end]:
                to_print += card
            print(self.players[i], ":", to_print)
            
    def do_round(self, uncovered):
        """
        Makes changes to the deck based on round.
        
        @param uncovered - an n-character string with what was uncovered.
        """
        assert len(uncovered) == self.num_players
        for card in uncovered:
            if card == 'C':
                print("Game over, cultists win!")
                self.num_cthulhu -= 1
            elif card == 'E':
                self.num_signs -= 1
            elif card == '-':
                self.num_blank -= 1
            else:
                print("Incorrect input!")
        self.create_deck()

