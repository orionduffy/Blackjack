import questionary
from deck import Deck
import socket
import threading
import pdb


# The main class for running the Blackjack game. Game will continue until the player either quits or runs out of money
class Blackjack:
    def __init__(self, connection):
        self.player_money: int = 100
        self.min_bet: int = 5

        self.deck = Deck()
        self.shuffled_deck = self.deck.shuffle_deck()

        self.player_cards = []
        self.dealer_cards = []

        self.conn = connection

    # Runs the main game loop, which potentially includes several rounds
    def run(self):
        choices = ["Continue", "Quit"]
        choice = choices[0]

        while self.player_money >= self.min_bet and choice == choices[0]:
            self.sendData(f"{OUTPUT_HEADER}You have ${self.player_money} to bet with!")
            self.sendData(f"{QUESTION_HEADER_INPUT}How much would you like to bet?,{self.player_money},{self.min_bet}")
            bet = int(self.receiveData())

            self.sendData(f"{OUTPUT_HEADER}${bet} will be bet! You have ${self.player_money - bet} left in reserve! Beginning game!")

            multiplier = self.run_round()
            self.reset_game()

            self.player_money += bet * multiplier
            self.player_money = int(self.player_money)
            self.sendData(f"{OUTPUT_HEADER}You now have ${self.player_money}!")

            if self.player_money >= self.min_bet:
                content = QUESTION_HEADER_CHOICE + ", ".join(choices)
                self.sendData(content)
                choice = self.receiveData()

        self.sendData(f"{OUTPUT_HEADER}Thank you for playing. You left with ${self.player_money}")

    def reset_game(self):
        self.shuffled_deck = self.deck.shuffle_deck()

        self.player_cards = []
        self.dealer_cards = []

    def print_player_info(self):
        self.sendData(f"{OUTPUT_HEADER}Your cards: {self.player_cards} \nPlayer Sum: {self.deck.sum_cards(self.player_cards)}")
    
    def print_dealer_info(self):
        self.sendData(f"{OUTPUT_HEADER}Dealer cards: {self.dealer_cards} \nDealer sum: {self.deck.sum_cards(self.dealer_cards)}")

    # Runs the loop for an individual rounds,
    # which at a basic level involves drawing new cards until the player stops or goes over 21
    def run_round(self):

        for i in range(2): 
            self.player_cards.append(self.shuffled_deck.pop(0))
            self.dealer_cards.append(self.shuffled_deck.pop(0))

        self.sendData(f"{OUTPUT_HEADER}Dealer's up card: {self.dealer_cards[0]} ({self.deck.base_deck[self.dealer_cards[0]]} points)")
        self.print_player_info()

        if self.deck.sum_cards(self.dealer_cards) != 21 and self.deck.sum_cards(self.player_cards) != 21:
            # Choices listed here because hardcoding is bad
            choices = ["Hit (Draw another card)",
                       "Stand (Keep your current hand)",
                       "Double (Double your original bet and get only 1 more card)",
                       "Surrender (Give up and get half your bet back)"
                       ]
            content = QUESTION_HEADER_CHOICE + ",".join(choices)
            self.sendData(content)
            choice = self.receiveData()

            while choice == choices[0]:

                self.player_cards.append(self.shuffled_deck.pop(0))
                self.print_player_info()

                if self.deck.sum_cards(self.player_cards) > 21: 
                    break

                content = QUESTION_HEADER_CHOICE + ",".join(choices[:-2])
                self.sendData(content)
                choice = self.receiveData()
                

            if choice == choices[2]:
                self.player_cards.append(self.shuffled_deck.pop(0))
                self.print_player_info()

            if self.deck.sum_cards(self.player_cards) <= 21 and choice != choices[-1]:
                self.sendData(f"{OUTPUT_HEADER}The dealer now flips over their hole card.")
                self.print_dealer_info()

                if self.deck.sum_cards(self.dealer_cards) < 17:
                    self.sendData(f"{OUTPUT_HEADER}The dealer has less than 17 points. he begins drawing.")
                    while self.deck.sum_cards(self.dealer_cards) < 17:
                        self.dealer_cards.append(self.shuffled_deck.pop(0))
                    self.print_dealer_info()

            self.sendData(f"{OUTPUT_HEADER}Game over!")
            return self.game_end(choices.index(choice))
        else:
            # If one person has a blackjack, the game immediately ends
            self.sendData(f"{OUTPUT_HEADER}Game immediately over!")
            return self.blackjack_end()

    # Handles a normal ending of the game
    def game_end(self, special=0):
        player_won = 0
        dealer_sum = self.deck.sum_cards(self.dealer_cards)
        player_sum = self.deck.sum_cards(self.player_cards)
        self.sendData(f"{OUTPUT_HEADER}The dealer has {dealer_sum} points and the player has {player_sum} points!")
        if special == 3:
            self.sendData(f"{OUTPUT_HEADER}The player chose to surrender! They get half their bet back!")
            player_won = -0.5
        elif player_sum > 21:
            self.sendData(f"{OUTPUT_HEADER}The player went bust! The player lost!")
            player_won = -1
        elif dealer_sum > 21:
            self.sendData(f"{OUTPUT_HEADER}The dealer went bust! The player won!")
            player_won = 1
        elif player_sum == dealer_sum:
            self.sendData(f"{OUTPUT_HEADER}The player and dealer have the same number of points! A push occurred!")
            player_won = 0
        elif player_sum > dealer_sum:
            self.sendData(f"{OUTPUT_HEADER}The player has more points than the dealer! The player won!")
            player_won = 1
        elif player_sum < dealer_sum:
            self.sendData(f"{OUTPUT_HEADER}The player has less points than the dealer! The dealer won!")
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
            self.sendData(f"{OUTPUT_HEADER}The player and dealer both have a blackjack! A push occurred!")
            return 0
        if dealer_sum == 21:
            self.sendData(f"{OUTPUT_HEADER}The dealer has a blackjack! Any player who does not have a blackjack has instantly lost!")
            return -1
        if player_sum == 21:
            self.sendData(f"{OUTPUT_HEADER}The player has a blackjack and the dealer does not! The player gets payed out 3 to 2!")
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
    
    def sendData(self, msg):
        global HEADER
        global FORMAT
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        self.conn.send(send_length)
        self.conn.send(message)
    
    def receiveData(self):
        global HEADER
        global FORMAT
        msg_length = self.conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = self.conn.recv(msg_length).decode(FORMAT)
            return msg
        return 0

HEADER = 64
PORT = 5050
SERVER = "172.19.93.54"
# SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNET_MESSAGE = "!DISCONNECT"
QUESTION_HEADER_CHOICE = "CHOOCE\n"
QUESTION_HEADER_INPUT = "IINPUT\n"
OUTPUT_HEADER = "OUTPUT\n"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)



def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    while True:
        blackjack = Blackjack(conn)
        blackjack.run()
        blackjack.sendData(DISCONNET_MESSAGE)
        conn.close()


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target = handle_client, args=(conn,addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount()-1}")

print("[STARTING] server is starting...")
start()
