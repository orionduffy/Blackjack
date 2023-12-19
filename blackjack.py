import questionary
from deck import Deck

from colorama import init as colorama_init
from colorama import Fore, Style


# The main class for running the Blackjack game. Game will continue until the player either quits or runs out of money
class Blackjack:
    """This class Blackjack game class for single player."""
    def __init__(self):
        """This function initialize the player money to $100 and set the environment ready to start game."""
        self.player_money: int = 100
        self.min_bet: int = 5

        self.deck = Deck()
        self.shuffled_deck = self.deck.shuffle_deck()

        self.player_cards = []
        self.dealer_cards = []

    # Runs the main game loop, which potentially includes several rounds
    def run(self):
        """
        This function get the betting amount from player before every game \
        started and calls the run_round function to handle the action of \
        player in every round. After single game is over, it adds or reducts the \
        won/loss amount to player's money. The Game re-runs till the players quits.
        """

        choices = ["Continue", "Quit"]
        choice = choices[0]

        while self.player_money >= self.min_bet and choice == choices[0]:
            print(f"{Fore.BLUE}You have ${self.player_money} to bet with!{Style.RESET_ALL}")
            bet = int(questionary.text("How much would you like to bet?", validate=self.validate_bet).ask())

            print(f"{Fore.BLUE}${bet} will be bet! You have ${self.player_money - bet} left in reserve! Beginning game!{Style.RESET_ALL}")

            multiplier = self.run_round()
            self.reset_game()

            self.player_money += bet * multiplier
            self.player_money = int(self.player_money)
            print(f"{Fore.BLUE}You now have ${self.player_money}!{Style.RESET_ALL}")

            if self.player_money >= self.min_bet:
                choice = questionary.select("What do you want to do?", choices=choices).ask()

        print(f"{Fore.GREEN}Thank you for playing. You left with ${self.player_money}{Style.RESET_ALL}")

    def reset_game(self):
        """This function reset some game variables before new game is started."""
        self.shuffled_deck = self.deck.shuffle_deck()

        self.player_cards = []
        self.dealer_cards = []

    # Runs the loop for an individual rounds,
    # which at a basic level involves drawing new cards until the player stops or goes over 21
    def run_round(self):
        """
        This function handles the actions of a players done after each round
        and does the necessary action based on that.
        """
        
        for i in range(2):
            self.player_cards.append(self.shuffled_deck.pop(0))

        for i in range(2):
            self.dealer_cards.append(self.shuffled_deck.pop(0))

        print(f"{Fore.YELLOW}Dealer's up card{Style.RESET_ALL}: {self.dealer_cards[0]} ({self.deck.base_deck[self.dealer_cards[0]]} points)")
        print(f"{Fore.YELLOW}Your cards{Style.RESET_ALL}: {self.player_cards}")
        print(f"{Fore.YELLOW}Sum{Style.RESET_ALL}: {self.deck.sum_cards(self.player_cards)}")

        if self.deck.sum_cards(self.dealer_cards) != 21 and self.deck.sum_cards(self.player_cards) != 21:
            # Choices listed here because hardcoding is bad
            choices = ["Hit (Draw another card)",
                       "Stand (Keep your current hand)",
                       "Double (Double your original bet and get only 1 more card)",
                       "Surrender (Give up and get half your bet back)"
                       ]
            choice = questionary.select("What do you want to do?", choices=choices).ask()

            while choice == choices[0]:

                self.player_cards.append(self.shuffled_deck.pop(0))

                print(f"{Fore.YELLOW}Your cards{Style.RESET_ALL}: {self.player_cards}")
                print(f"{Fore.YELLOW}Sum{Style.RESET_ALL}: {self.deck.sum_cards(self.player_cards)}")

                if self.deck.sum_cards(self.player_cards) > 21:
                    break

                choice = questionary.select("What do you want to do next?", choices=choices[:-2]).ask()

            if choice == choices[2]:
                self.player_cards.append(self.shuffled_deck.pop(0))

                print(f"{Fore.YELLOW}Your cards{Style.RESET_ALL}: {self.player_cards}")
                print(f"{Fore.YELLOW}Sum{Style.RESET_ALL}: {self.deck.sum_cards(self.player_cards)}")

            if self.deck.sum_cards(self.player_cards) <= 21 and choice != choices[-1]:
                print(f"{Fore.BLUE}The dealer now flips over their hole card.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Dealer cards{Style.RESET_ALL}: {self.dealer_cards}")
                print(f"{Fore.YELLOW}Dealer sum{Style.RESET_ALL}: {self.deck.sum_cards(self.dealer_cards)}")

                if self.deck.sum_cards(self.dealer_cards) < 17:
                    print("The dealer has less than 17 points. he begins drawing.")

                while self.deck.sum_cards(self.dealer_cards) < 17:
                    self.dealer_cards.append(self.shuffled_deck.pop(0))
                    print(f"{Fore.YELLOW}Dealer cards{Style.RESET_ALL}: {self.dealer_cards}")
                    print(f"{Fore.YELLOW}Dealer sum{Style.RESET_ALL}: {self.deck.sum_cards(self.dealer_cards)}")

            print(f"{Fore.GREEN}Game over!{Style.RESET_ALL}")
            return self.game_end(choices.index(choice))
        else:
            # If one person has a blackjack, the game immediately ends
            print(f"{Fore.GREEN}Game immediately over!{Style.RESET_ALL}")
            return self.blackjack_end()

    # Handles a normal ending of the game
    def game_end(self, special=0):
        """
        This function checks if a player won/lost after the game is over
        and calculates the bet multiplier amount for the player.
        
        Args:
            special (int, default=0): index of choice of player from the choice provided 

        Returns:
                int: multiplier to the betting amount
        """ 
        player_won = 0
        print(
            f"The dealer has {self.deck.sum_cards(self.dealer_cards)} points and the player has {self.deck.sum_cards(self.player_cards)} points!")
        if special == 3:
            print(f"{Fore.YELLOW}The player chose to surrender! They get half their bet back!{Style.RESET_ALL}")
            player_won = -0.5
        elif self.deck.sum_cards(self.player_cards) > 21:
            print(f"{Fore.RED}The player went bust! The player lost!{Style.RESET_ALL}")
            player_won = -1
        elif self.deck.sum_cards(self.dealer_cards) > 21:
            print(f"{Fore.BLUE}The dealer went bust! The player won!{Style.RESET_ALL}")
            player_won = 1
        elif self.deck.sum_cards(self.player_cards) == self.deck.sum_cards(self.dealer_cards):
            print(f"{Fore.YELLOW}The player and dealer have the same number of points! A push occurred!{Style.RESET_ALL}")
            player_won = 0
        elif self.deck.sum_cards(self.player_cards) > self.deck.sum_cards(self.dealer_cards):
            print(f"{Fore.BLUE}The player has more points than the dealer! The player won!{Style.RESET_ALL}")
            player_won = 1
        elif self.deck.sum_cards(self.player_cards) < self.deck.sum_cards(self.dealer_cards):
            print(f"{Fore.RED}The player has less points than the dealer! The dealer won!{Style.RESET_ALL}")
            player_won = -1

        if special == 2:
            player_won *= 2

        return player_won

    # Handles ending the game if someone got a blackjack
    def blackjack_end(self):
        """This function checks if there is a blackjack win after the first two cards are given to the player."""
        
        player_won = 0

        if self.deck.sum_cards(self.player_cards) == 21 and self.deck.sum_cards(self.dealer_cards) == 21:
            print(f"{Fore.YELLOW}The player and dealer both have a blackjack! A push occurred!{Style.RESET_ALL}")
            player_won = 0
        elif self.deck.sum_cards(self.dealer_cards) == 21:
            print(f"{Fore.RED}The dealer has a blackjack! Any player who does not have a blackjack has instantly lost!")
            player_won = -1
        elif self.deck.sum_cards(self.player_cards) == 21:
            print(f"{Fore.BLUE}The player has a blackjack and the dealer does not! The player gets payed out 3 to 2!{Style.RESET_ALL}")
            player_won = 2.5

        return player_won

    # Handles the text validation when a user attempts to make a bet
    def validate_bet(self, text):
        """This function checks the input data provided to see if the player has sufficient money for the bet.
    
        Args:
            text (String): input text

        Returns:
                boolean: True if text is enough amount for the bet else it return a string to notify bet is invalid.
        """
        try:
            bet = int(text)
            if bet > self.player_money:
                return "You don't have that much money! Please enter a lower amount"
            elif bet < self.min_bet:
                return "The minimum bet is $5"
            else:
                return True
        except ValueError:
            return "Please enter a number"