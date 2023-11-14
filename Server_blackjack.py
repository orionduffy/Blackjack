import questionary
from deck import Deck
import socket
import threading
import pdb
import copy
from Server_Player_Info import Player


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
lock = threading.Lock()


# The main class for running the Blackjack game. Game will continue until the player either quits or runs out of money
class Blackjack:
    def __init__(self, players):
        self.min_bet: int = 5

        self.deck = Deck()
        self.shuffled_deck = self.deck.shuffle_deck()

        self.players_list = players
        self.activePlayers = [n for n in range(len(self.players_list))]   # at first all players are active
        self.dealer_cards = []


    # Runs the main game loop, which potentially includes several rounds
    def run(self):
               
        # def subFunction(self):
        bets = [0] * len(self.players_list)  # this will hold individual bets of every player

        # while self.players_money >= self.min_bet and choice == choices[0]:
        threads = []
        for k in self.activePlayers:
            if self.players_list[k].player_money >= self.min_bet :
                th = threading.Thread(target=self.thread1, args=(k, bets))
                threads.append(th)
                th.start()
        for th in threads: th.join()
        threads.clear()
        self.broadcast("bet_amount", bets)

        multipliers = self.run_round()
        self.reset_game()

        for k in self.activePlayers:
            self.players_list[k].player_money += bets[k] * multipliers[k]
            self.players_list[k].player_money = int(self.players_list[k].player_money)
            self.sendData(k, f"{OUTPUT_HEADER}You now have ${self.players_list[k].player_money}!")

        # going for the next round and asking the player if they want to play or not
        for k in range(len(self.activePlayers)):
            th = threading.Thread(target=self.thread3, args=(k,))
            threads.append(th)
            th.start()
        for th in threads: th.join()
        
        
        temp = [ self.players_list[self.activePlayers[k]].name for k in range(len(self.activePlayers)) if self.activePlayers[k] == -1]
        self.broadcast("continue_quit", temp)
        self.activePlayers = [k for k in self.activePlayers if k != -1]

        
        if len(self.activePlayers) == 0:
            self.broadcast('score_board')
        elif len(self.activePlayers) > 0: 
            self.run()

    # Runs the loop for an individual rounds,
    # which at a basic level involves drawing new cards until the player stops or goes over 21
    def run_round(self):

        for i in range(2): 
            self.dealer_cards.append(self.shuffled_deck.pop(0))
            for k in self.activePlayers:
                self.players_list[k].player_cards.append(self.shuffled_deck.pop(0))
                
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

        # first_round is used to send the player either all 4 choices or first two choices
        first_round = True
        while True:
            #the flag indicate if the current game come to end and if True the while loop will terminate
            flag = [True]
            threads = []
            for k in self.activePlayers:
                if self.players_list[k].status == choices[0]:
                    th = threading.Thread(target=self.thread2, args=(k, flag, first_round, choices))
                    threads.append(th)
                    th.start()
            for th in threads: th.join()
            
            self.broadcast("turn_action")

            if flag[0]:
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


    def reset_game(self):
        self.shuffled_deck = self.deck.shuffle_deck()

        for pl in self.players_list: pl.initialize_new_game()
        self.dealer_cards = []

    def print_player_info(self, ind):
        self.sendData(ind, f"{OUTPUT_HEADER}Your cards: {self.players_list[ind].player_cards} \nPlayer Sum: {self.deck.sum_cards(self.players_list[ind].player_cards)}")
    
    def print_dealer_info(self, ind):
        self.sendData(ind, f"{OUTPUT_HEADER}Dealer cards: {self.dealer_cards} \nDealer sum: {self.deck.sum_cards(self.dealer_cards)}")

    #handles the process of getting bet amount from the players
    def thread1(self, k, bets):
        self.sendData(k, f"{OUTPUT_HEADER}You have ${self.players_list[k].player_money} to bet with!")
        self.sendData(k, f"{QUESTION_HEADER_INPUT} How much would you like to bet?,{self.players_list[k].player_money},{self.min_bet}")
        bets[k] = int(self.receiveData(k))
        self.sendData(k, f"{OUTPUT_HEADER}${bets[k]} will be bet! You have ${self.players_list[k].player_money - bets[k]} left in reserve! Beginning game!")
  
    #handles the process of getting the player's turn choice and do the relevant action
    def thread2(self, k, flag, first_round, choices):
        
            content = QUESTION_HEADER_CHOICE + ",".join(choices[:-2])
            if first_round:
                content = QUESTION_HEADER_CHOICE + ",".join(choices)
            self.sendData(k, content)
            self.players_list[k].status = self.receiveData(k)
            if self.players_list[k].status == choices[0]:
                self.players_list[k].player_cards.append(self.shuffled_deck.pop(0))
                self.print_player_info(k)

                if self.deck.sum_cards(self.players_list[k].player_cards) > 21: 
                    self.sendData(k, f"{OUTPUT_HEADER}Your are Busted.")
                    self.players_list[k].status = "Bust"

                if self.players_list[k].status == choices[0]:
                    flag[0] = False
            if self.players_list[k].status == choices[2]:
                self.players_list[k].player_cards.append(self.shuffled_deck.pop(0))
                self.print_player_info(k)

    #Handles if the player wants to continue or quit
    def thread3(self, k):
        choices = ["Continue", "Quit"]
        choice = ""
        current = self.activePlayers[k]
        if self.players_list[current].player_money >= self.min_bet:
            content = QUESTION_HEADER_CHOICE + ",".join(choices)
            self.sendData(current, content)
            choice = self.receiveData(current)                  
        if self.players_list[current].player_money < self.min_bet or choice == choices[1]:
            self.sendData(current, f"{OUTPUT_HEADER}Thank you for playing. You left with ${self.players_list[current].player_money}")
            self.activePlayers[k] = -1
        
    # Handles a normal ending of the game
    def game_end(self, choices):
        multipliers = [0] * len(self.players_list)
        dealer_sum = self.deck.sum_cards(self.dealer_cards)
        players_sum = [self.deck.sum_cards(li.player_cards) for li in self.players_list]
        choice_copy = copy.deepcopy(choices)
        values_to_append = ["Push", "Lost", "BlackJack", "Bust"]
        choice_copy = choice_copy + values_to_append
        for k in self.activePlayers:
            special = choice_copy.index(self.players_list[k].status)
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
        player_sum = [self.deck.sum_cards(li.player_cards) for li in self.players_list]
        
        for k in self.activePlayers:
            #returns the player multiplier by checking who the winner of the game is
            if player_sum[k] == 21 and dealer_sum == 21:
                self.sendData(k, f"{OUTPUT_HEADER}The player and dealer both have a blackjack! A push occurred!")
                self.players_list[k].status = "Push"
            if dealer_sum == 21:
                self.sendData(k, f"{OUTPUT_HEADER}The dealer has a blackjack! Any player who does not have a blackjack has instantly lost!")
                self.players_list[k].status = "Lost"
            if player_sum[k] == 21:
                self.sendData(k, f"{OUTPUT_HEADER}The player has a blackjack and the dealer does not! The player gets payed out 3 to 2!")
                self.players_list[k].status = "BlackJack"

    def broadcast(self, message_type, li=[]):
        if message_type == "score_board":
            # sorting players list according to thier final money amount
            self.players_list.sort(key=lambda x: x.player_money, reverse=True)
            
            name_and_money = [str(p) + ". " + self.players_list[p].name.ljust(10) + "$" + str(self.players_list[p].player_money) for p in range(len(self.players_list))]
            board_data = "SCORE BOARD".center(30) + "\n" + "\n".join(name_and_money) + "\n"

            broadcast_messsage = OUTPUT_HEADER + board_data
        
        elif message_type == "turn_action":
            players_action = [self.players_list[p].name + " -> " + self.players_list[p].status  for p in self.activePlayers]
            broadcast_messsage = OUTPUT_HEADER + "Players Turn Action\n" + "\n".join(players_action) + "\n"
        
        elif message_type == "continue_quit":
            players_action = [p + " -> " + "quit Game"  for p in li]
            broadcast_messsage = OUTPUT_HEADER + "\nPlayers who quit Game\n" + "\n".join(players_action) + "\n"

        elif message_type == "bet_amount":
            players_bet_amount = [self.players_list[p].name + " -> $" + str(li[p])  for p in self.activePlayers]
            broadcast_messsage = OUTPUT_HEADER + "\nPlayers Betting Money\n" + "\n".join(players_bet_amount) + "\n"
        
        for k in range(len(self.players_list)):
            self.sendData(k, broadcast_messsage)

    def sendData(self, ind, msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        self.players_list[ind].conn.send(send_length)
        self.players_list[ind].conn.send(message)
    
    def receiveData(self, ind):
        msg_length = self.players_list[ind].conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = self.players_list[ind].conn.recv(msg_length).decode(FORMAT)
            return msg
        return 0
