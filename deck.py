import random

# The class responsible for managing the deck itself.
# Creates the base deck that everything is based on, and contains functions that require said base deck.
class Deck:
    """This class represents the deck of cards which will be used in the Blackjack game."""
    def __init__(self):
        """This function initializes the deck with its full cards."""
        self.card_types = ['\u2663', '\u2660', '\u2665', '\u2666']
        self.card_num = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        self.value = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]

        # this deck of cards is initiated at the start of the session and is not used in play.
        # A deck of keys is used instead.
        self.base_deck = {self.card_num[j] + n: self.value[j]
                          for n in self.card_types for j in range(len(self.card_num))}

    # https://pynative.com/python-random-shuffle/#:~:text=Shuffling%20a%20dictionary%20is%20not,dictionary%20values%20using%20shuffled%20keys.
    #  This function is used to shuffle the deck of cards dictionary and is called after every new game
    def shuffle_deck(self):
        """
        This function shuffles the deck of cards
        and insert the element of randomness into the order of the deck of cards.
        
        Returns:
                list of string: list of the keys to the deck of cards"""
        keys = list(self.base_deck.keys())
        random.shuffle(keys)
        return keys

    # This method accept the deck keys only and it figures their values by itself and calculates the sum
    def sum_cards(self, cards):
        """
        This function finds the sum of the cards provided as parameter and returns the amount.
        
        Args:
            cards (list): list of cards
            
        Returns:
                int: sum of the cards
        
        """
        values = [self.base_deck[card] for card in cards]
        point_sum = sum(values)
        aces = values.count(11)

        for i in range(aces):
            if point_sum > 21:
                point_sum -= 10

        return point_sum