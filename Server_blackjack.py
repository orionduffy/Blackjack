import questionary
from deck import Deck
import socket
import threading
import pdb
import copy


HEADER = 64
PORT = 5050
# SERVER = "172.19.93.54"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNET_MESSAGE = "!DISCONNECT"
QUESTION_HEADER_CHOICE = "CHOOCE\n"
QUESTION_HEADER_INPUT = "IINPUT\n"
OUTPUT_HEADER = "OUTPUT\n"


# The main class for running the Blackjack game. Game will continue until the player either quits or runs out of money
class Blackjack:
    def __init__(self, connections):
        self.players_money = [100] * len(connections)
        self.min_bet: int = 5

        self.deck = Deck()
        self.shuffled_deck = self.deck.shuffle_deck()

        self.players_cards = [[] for _ in range(len(connections))]
        self.activePlayers = [n for n in range(len(connections))]
        self.dealer_cards = []

        self.conns = connections
        self.status = ["Hit (Draw another card)"] * len(connections)   # this indicates if the player wants hit or stand or something else
       

    # Runs the main game loop, which potentially includes several rounds
    def run(self):
        choices = ["Continue", "Quit"]
        choice = choices[0]
        
        # def subFunction(self):
        bets = [0] * len(self.conns)  # this will hold individual bets of every player

        # while self.players_money >= self.min_bet and choice == choices[0]:
        for k in self.activePlayers:
            if self.players_money[k] >= self.min_bet :
                self.sendData(k, f"{OUTPUT_HEADER}You have ${self.players_money[k]} to bet with!")
                self.sendData(k, f"{QUESTION_HEADER_INPUT}{k} How much would you like to bet?,{self.players_money[k]},{self.min_bet}")
                bets[k] = int(self.receiveData(k))

                self.sendData(k, f"{OUTPUT_HEADER}${bets[k]} will be bet! You have ${self.players_money[k] - bets[k]} left in reserve! Beginning game!")

        multipliers = self.run_round()
        self.reset_game()

        for k in self.activePlayers:
            self.players_money[k] += bets[k] * multipliers[k]
            self.players_money[k] = int(self.players_money[k])
            self.sendData(k, f"{OUTPUT_HEADER}You now have ${self.players_money[k]}!")

        k = 0  # Initialize index variable
        while k < len(self.activePlayers):
        # for k in range(len(self.activePlayers)):
            print(self.activePlayers, "  ", k)  
            choice = ""
            current = self.activePlayers[k]
            if self.players_money[current] >= self.min_bet:
                content = QUESTION_HEADER_CHOICE + ",".join(choices)
                self.sendData(current, content)
                choice = self.receiveData(current)                  
            if self.players_money[current] < self.min_bet or choice == choices[1]:
                self.sendData(current, f"{OUTPUT_HEADER}Thank you for playing. You left with ${self.players_money[current]}")
                self.activePlayers.pop(k)
            else: k +=1

        print(self.activePlayers)
        if len(self.activePlayers) > 0: 
            print("New Game Started>>")
            self.run()

    def reset_game(self):
        self.shuffled_deck = self.deck.shuffle_deck()

        self.players_cards = [[] for _ in range(len(self.conns))]
        self.dealer_cards = []

        self.status = ["Hit (Draw another card)"] * len(self.conns)   # this indicates if the player wants hit or stand or something else

    def print_player_info(self, ind):
        self.sendData(ind, f"{OUTPUT_HEADER}Your cards: {self.players_cards[ind]} \nPlayer Sum: {self.deck.sum_cards(self.players_cards[ind])}")
    
    def print_dealer_info(self, ind):
        self.sendData(ind, f"{OUTPUT_HEADER}Dealer cards: {self.dealer_cards} \nDealer sum: {self.deck.sum_cards(self.dealer_cards)}")

    # Runs the loop for an individual rounds,
    # which at a basic level involves drawing new cards until the player stops or goes over 21
    def run_round(self):

        for i in range(2): 
            self.dealer_cards.append(self.shuffled_deck.pop(0))
            for k in self.activePlayers:
                self.players_cards[k].append(self.shuffled_deck.pop(0))
                
        for k in self.activePlayers:
            self.sendData(k, f"{OUTPUT_HEADER}Dealer's up card: {self.dealer_cards[0]} ({self.deck.base_deck[self.dealer_cards[0]]} points)")
            self.print_player_info(k)

        # if self.deck.sum_cards(self.dealer_cards) != 21:# and self.deck.sum_cards(self.players_cards[0]) != 21:
        self.blackjack_check()
        # Choices listed here because hardcoding is bad
        choices = ["Hit (Draw another card)",
                    "Stand (Keep your current hand)",
                    "Double (Double your original bet and get only 1 more card)",
                    "Surrender (Give up and get half your bet back)"
                    ]
        first_round = True
        while True:
            flag = True
            for k in self.activePlayers:
            # while choice == choices[0]:
                if self.status[k] == choices[0]:
                    content = QUESTION_HEADER_CHOICE + ",".join(choices[:-2])
                    if first_round:
                        content = QUESTION_HEADER_CHOICE + ",".join(choices)
                    self.sendData(k, content)
                    self.status[k] = self.receiveData(k)
                    if self.status[k] == choices[0]:
                        self.players_cards[k].append(self.shuffled_deck.pop(0))
                        self.print_player_info(k)

                        if self.deck.sum_cards(self.players_cards[k]) > 21: 
                            self.sendData(k, f"{OUTPUT_HEADER}Your are Busted.")
                            self.status[k] = "Bust"

                        if self.status[k] == choices[0]:
                            flag = False
                    if self.status[k] == choices[2]:
                        self.players_cards[k].append(self.shuffled_deck.pop(0))
                        self.print_player_info(k)
            if flag:
                break
            first_round = False

        

        # if self.deck.sum_cards(self.players_cards) <= 21 and choice != choices[-1]:
        for k in self.activePlayers:
            self.sendData(k, f"{OUTPUT_HEADER}The dealer now flips over their hole card.")
            self.print_dealer_info(k)
        
        
        if self.deck.sum_cards(self.dealer_cards) < 17:
            while self.deck.sum_cards(self.dealer_cards) < 17:
                self.dealer_cards.append(self.shuffled_deck.pop(0))
            for k in self.activePlayers: 
                self.sendData(k, f"{OUTPUT_HEADER}The dealer has less than 17 points. he begins drawing.")
                self.print_dealer_info(k)

        for k in self.activePlayers: self.sendData(k, f"{OUTPUT_HEADER}Game over!")
        return self.game_end(choices)
        # else:
        #     # If one person has a blackjack, the game immediately ends
        #     self.sendData(f"{OUTPUT_HEADER}Game immediately over!")
        #     return self.blackjack_end()

    # Handles a normal ending of the game
    def game_end(self, choices):
        multipliers = [0] * len(self.conns)
        dealer_sum = self.deck.sum_cards(self.dealer_cards)
        players_sum = [self.deck.sum_cards(li) for li in self.players_cards]
        choice_copy = copy.deepcopy(choices)
        values_to_append = ["Push", "Lost", "BlackJack", "Bust"]
        choice_copy = choice_copy + values_to_append
        for k in self.activePlayers:
            special = choice_copy.index(self.status[k])
            self.sendData(k, f"{OUTPUT_HEADER}The dealer has {dealer_sum} points and the player has {players_sum[k]} points!")
            if special == 4:
                multipliers[k] = 0
            elif special == 5:
                multipliers[k] = -1  
            elif special == 6:
                multipliers[k] = 2.5         
            elif special == 3:
                self.sendData(k, f"{OUTPUT_HEADER}The player chose to surrender! They get half their bet back!")
                multipliers[k] = -0.5
            elif players_sum[k] > 21:
                self.sendData(k, f"{OUTPUT_HEADER}The player went bust! The player lost!")
                multipliers[k] = -1
            elif dealer_sum > 21:
                self.sendData(k, f"{OUTPUT_HEADER}The dealer went bust! The player won!")
                multipliers[k] = 1
            elif players_sum[k] == dealer_sum:
                self.sendData(k, f"{OUTPUT_HEADER}The player and dealer have the same number of points! A push occurred!")
                multipliers[k] = 0
            elif players_sum[k] > dealer_sum:
                self.sendData(k, f"{OUTPUT_HEADER}The player has more points than the dealer! The player won!")
                multipliers[k] = 1
            elif players_sum[k] < dealer_sum:
                self.sendData(k, f"{OUTPUT_HEADER}The player has less points than the dealer! The dealer won!")
                multipliers[k] = -1

            if special == 2:
                multipliers[k] *= 2

        return multipliers

    # Handles ending the game if someone got a blackjack
    def blackjack_check(self):
        
        dealer_sum = self.deck.sum_cards(self.dealer_cards)
        player_sum = [self.deck.sum_cards(li) for li in self.players_cards]
        
        for k in self.activePlayers:
            #returns the player multiplier by checking who the winner of the game is
            if player_sum[k] == 21 and dealer_sum == 21:
                self.sendData(k, f"{OUTPUT_HEADER}The player and dealer both have a blackjack! A push occurred!")
                self.status[k] = "Push"
            if dealer_sum == 21:
                self.sendData(k, f"{OUTPUT_HEADER}The dealer has a blackjack! Any player who does not have a blackjack has instantly lost!")
                self.status[k] = "Lost"
            if player_sum[k] == 21:
                self.sendData(k, f"{OUTPUT_HEADER}The player has a blackjack and the dealer does not! The player gets payed out 3 to 2!")
                self.status[k] = "BlackJack"

    # Handles the text validation when a user attempts to make a bet
    def validate_bet(self, text):
        try:
            bet = int(text)
            if bet > self.players_money:
                return "You don't have that much money! Please enter a lower amount"
            elif bet < self.min_bet:
                return "The minimum bet is $5"
            else:
                return True
        except ValueError:
            return "Please enter a number"
    
    def sendData(self, ind, msg):
        global HEADER
        global FORMAT
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        self.conns[ind].send(send_length)
        self.conns[ind].send(message)
    
    def receiveData(self, ind):
        global HEADER
        global FORMAT
        msg_length = self.conns[ind].recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = self.conns[ind].recv(msg_length).decode(FORMAT)
            return msg
        return 0
