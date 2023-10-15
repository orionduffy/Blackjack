import questionary
from deck import Deck


# The main class for running the Blackjack game. Game will continue until the player either quits or runs out of money
class Blackjack:
    def __init__(self):
        self.player_money: int = 100
        self.min_bet: int = 5

        self.deck = Deck()
        self.shuffled_deck = self.deck.shuffle_deck()

        self.player_cards = []
        self.dealer_cards = []

    # Runs the main game loop, which potentially includes several rounds
    def run(self):
        choices = ["Continue", "Quit"]
        choice = choices[0]

        while self.player_money >= self.min_bet and choice == choices[0]:
            print(f"You have ${self.player_money} to bet with!")
            bet = int(questionary.text("How much would you like to bet?", validate=self.validate_bet).ask())

            print(f"${bet} will be bet! You have ${self.player_money - bet} left in reserve! Beginning game!")

            multiplier = self.run_round()
            self.reset_game()

            self.player_money += bet * multiplier
            self.player_money = int(self.player_money)
            print(f"You now have ${self.player_money}!")

            if self.player_money >= self.min_bet:
                choice = questionary.select("What do you want to do?", choices=choices).ask()

        print(f"Thank you for playing. You left with ${self.player_money}")

    def reset_game(self):
        self.shuffled_deck = self.deck.shuffle_deck()

        self.player_cards = []
        self.dealer_cards = []

    def print_player_info(self):
        print(f"Your cards: {self.player_cards} \nPlayer Sum: {self.deck.sum_cards(self.player_cards)}")
    
    def print_dealer_info(self):
        print(f"Dealer cards: {self.dealer_cards} \nDealer sum: {self.deck.sum_cards(self.dealer_cards)}")

    # Runs the loop for an individual rounds,
    # which at a basic level involves drawing new cards until the player stops or goes over 21
    def run_round(self):

        for i in range(2): 
            self.player_cards.append(self.shuffled_deck.pop(0))
            self.dealer_cards.append(self.shuffled_deck.pop(0))

        print(f"Dealer's up card: {self.dealer_cards[0]} ({self.deck.base_deck[self.dealer_cards[0]]} points)")
        self.print_player_info()

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
                self.print_player_info()

                if self.deck.sum_cards(self.player_cards) > 21: 
                    break

                choice = questionary.select("What do you want to do next?", choices=choices[:-2]).ask()

            if choice == choices[2]:
                self.player_cards.append(self.shuffled_deck.pop(0))
                self.print_player_info()

            if self.deck.sum_cards(self.player_cards) <= 21 and choice != choices[-1]:
                print("The dealer now flips over their hole card.")
                self.print_dealer_info()

                if self.deck.sum_cards(self.dealer_cards) < 17:
                    print("The dealer has less than 17 points. he begins drawing.")
                    while self.deck.sum_cards(self.dealer_cards) < 17:
                        self.dealer_cards.append(self.shuffled_deck.pop(0))
                    self.print_dealer_info()

            print("Game over!")
            return self.game_end(choices.index(choice))
        else:
            # If one person has a blackjack, the game immediately ends
            print("Game immediately over!")
            return self.blackjack_end()

    # Handles a normal ending of the game
    def game_end(self, special=0):
        player_won = 0
        dealer_sum = self.deck.sum_cards(self.dealer_cards)
        player_sum = self.deck.sum_cards(self.player_cards)
        print(f"The dealer has {dealer_sum} points and the player has {player_sum} points!")
        if special == 3:
            print("The player chose to surrender! They get half their bet back!")
            player_won = -0.5
        elif player_sum > 21:
            print("The player went bust! The player lost!")
            player_won = -1
        elif dealer_sum > 21:
            print("The dealer went bust! The player won!")
            player_won = 1
        elif player_sum == dealer_sum:
            print("The player and dealer have the same number of points! A push occurred!")
            player_won = 0
        elif player_sum > dealer_sum:
            print("The player has more points than the dealer! The player won!")
            player_won = 1
        elif player_sum < dealer_sum:
            print("The player has less points than the dealer! The dealer won!")
            player_won = -1

        if special == 2:
            player_won *= 2

        return player_won

    # Handles ending the game if someone got a blackjack
    def blackjack_end(self):
        
        dealer_sum = self.deck.sum_cards(self.dealer_cards)
        player_sum = self.deck.sum_cards(self.player_cards)

        #returns the player multiplier by checking who the winner of the game is
        if player_sum == 21 and dealer_sum == 21:
            print("The player and dealer both have a blackjack! A push occurred!")
            return 0
        if dealer_sum == 21:
            print("The dealer has a blackjack! Any player who does not have a blackjack has instantly lost!")
            return -1
        if player_sum == 21:
            print("The player has a blackjack and the dealer does not! The player gets payed out 3 to 2!")
            return 2.5

    # Handles the text validation when a user attempts to make a bet
    def validate_bet(self, text):
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
