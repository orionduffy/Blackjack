import questionary
from deck import Deck
import socket
import threading
import pdb
import copy
from Server_Player_Info import Player
import logging

HEADER = 64
PORT = 5050
# SERVER = "172.19.93.54"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
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
        self.connected_players = list(filter(lambda player: player.connected, self.players_list))
        self.active_players = list(filter(lambda player: player.connected and player.active, self.connected_players))
        self.dealer_cards = []

        logging.debug("Blackjack class initialized")

    def refresh_player_lists(self):
        self.connected_players = list(filter(lambda player: player.connected, self.players_list))
        self.active_players = list(filter(lambda player: player.active, self.connected_players))

    # Runs the main game loop, which potentially includes several rounds
    def run(self):
        self.refresh_player_lists()

        # def subFunction(self):
        bets = [0] * len(self.active_players)  # this will hold individual bets of every player

        # while self.players_money >= self.min_bet and choice == choices[0]:
        threads = []
        for idx, player in enumerate(self.active_players):
            if player.player_money >= self.min_bet:
                th = threading.Thread(target=self.thread1, args=(idx, player, bets))
                threads.append(th)
                th.start()
        for th in threads: th.join()
        threads.clear()
        self.broadcast("bet_amount", bets)

        multipliers = self.run_round()
        self.reset_game()

        for idx, player in enumerate(self.active_players):
            player.player_money += bets[idx] * multipliers[idx]
            player.player_money = int(player.player_money)
            self.try_send_data(player, f"{OUTPUT_HEADER}You now have ${player.player_money}!")

        # going for the next round and asking the player if they want to play or not
        for player in self.active_players:
            th = threading.Thread(target=self.thread3, args=(player,))
            threads.append(th)
            th.start()
        for th in threads: th.join()

        temp = [player for player in self.players_list if
                player not in self.active_players]
        self.broadcast("continue_quit", temp)

        if len(self.active_players) == 0:
            self.broadcast('score_board')
        elif len(self.active_players) > 0:
            self.run()

    # Runs the loop for an individual rounds,
    # which at a basic level involves drawing new cards until the player stops or goes over 21
    def run_round(self):

        for i in range(2):
            self.dealer_cards.append(self.shuffled_deck.pop(0))
            for player in self.active_players:
                player.player_cards.append(self.shuffled_deck.pop(0))

        for player in self.active_players:
            self.try_send_data(player,
                           f"{OUTPUT_HEADER}Dealer's up card: {self.dealer_cards[0]} ({self.deck.base_deck[self.dealer_cards[0]]} points)")
            self.print_player_info(player)

        # if self.deck.sum_cards(self.dealer_cards) != 21:# and self.deck.sum_cards(self.players_cards[0]) != 21:
        self.blackjack_check()
        # Choices listed here because hardcoding is bad
        choices = ["Hit (Draw another card)",
                   "Stand (Keep your current hand)",
                   "Double (Double your original bet and get only 1 more card)",
                   "Surrender (Give up and get half your bet back)"
                   ]

        # first_round is used to sendall the player either all 4 choices or first two choices
        first_round = True
        while True:
            # the flag indicate if the current game come to end and if True the while loop will terminate
            break_loop = [True]
            threads = []
            for player in self.active_players:
                if player.status == choices[0]:
                    th = threading.Thread(target=self.thread2, args=(player, first_round, choices))
                    threads.append(th)
                    th.start()
            for th in threads: th.join()

            for player in self.active_players:
                if player.status == choices[0]:
                    player.player_cards.append(self.shuffled_deck.pop(0))

                    if self.deck.sum_cards(player.player_cards) > 21:
                        self.try_send_data(player, f"{OUTPUT_HEADER}You went Bust.")
                        player.status = "Bust"

                    if player.status == choices[0]:
                        break_loop[0] = False
                if player.status == choices[2]:
                    player.player_cards.append(self.shuffled_deck.pop(0))

            self.broadcast("turn_action")
            for player in self.active_players:
                self.print_player_info(player)

            if break_loop[0]:
                break
            first_round = False

        # if self.deck.sum_cards(self.players_cards) <= 21 and choice != choices[-1]:
        for player in self.connected_players:
            self.try_send_data(player, f"{OUTPUT_HEADER}The dealer now flips over their hole card.")
            self.print_dealer_info(player)

        if self.deck.sum_cards(self.dealer_cards) < 17:
            while self.deck.sum_cards(self.dealer_cards) < 17:
                self.dealer_cards.append(self.shuffled_deck.pop(0))
            for player in self.active_players:
                self.try_send_data(player, f"{OUTPUT_HEADER}The dealer has less than 17 points. he begins drawing.")
                self.print_dealer_info(player)

        for player in self.active_players: self.try_send_data(player, f"{OUTPUT_HEADER}Game over!")
        return self.game_end(choices)
        # else:
        #     # If one person has a blackjack, the game immediately ends
        #     self.try_send_data(f"{OUTPUT_HEADER}Game immediately over!")
        #     return self.blackjack_end()

    def reset_game(self):
        self.shuffled_deck = self.deck.shuffle_deck()

        for pl in self.players_list: pl.initialize_new_game()
        self.dealer_cards = []

    def print_player_info(self, player):
        self.try_send_data(player,
                       f"{OUTPUT_HEADER}Your cards: {player.player_cards} \nPlayer Sum: {self.deck.sum_cards(player.player_cards)}")

    def print_dealer_info(self, ind):
        self.try_send_data(ind,
                       f"{OUTPUT_HEADER}Dealer cards: {self.dealer_cards} \nDealer sum: {self.deck.sum_cards(self.dealer_cards)}")

    # handles the process of getting bet amount from the players
    def thread1(self, idx, player, bets):
        self.try_send_data(player, f"{OUTPUT_HEADER}You have ${player.player_money} to bet with!")
        self.try_send_data(player,
                       f"{QUESTION_HEADER_INPUT} How much would you like to bet?,"
                       f"{player.player_money},{self.min_bet}")
        bet_attempt = self.try_receive_data(player)
        try:
            if bet_attempt:
                bets[idx] = int(bet_attempt)
            else:
                bets.pop(idx)
        except ValueError:
            msg = f"Player {player.name}'s machine attempted to send an invalid input to the server.\n"\
                  f"There may be a bug, or the player may have modified the program."
            logging.error(msg)
            print(msg)

        self.try_send_data(player,
                       f"{OUTPUT_HEADER}${bets[idx]} will be bet! "
                       f"You have ${player.player_money - bets[idx]} left in reserve! "
                       f"Beginning game!")

    # handles the process of getting the player's turn choice and do the relevant action
    def thread2(self, player, first_round, choices):
        if first_round:
            content = QUESTION_HEADER_CHOICE + ",".join(choices)
        else:
            content = QUESTION_HEADER_CHOICE + ",".join(choices[:-2])

        self.try_send_data(player, content)
        received_data = self.try_receive_data(player)
        logging.debug(f"Turn choice received from {player.name}: {str(received_data)}")
        player.status = received_data if received_data else choices[1]

    # Handles if the player wants to continue or quit
    def thread3(self, player):
        choices = ["Continue", "Stop Betting", "Quit Game Completely"]
        choice = ""
        if player.player_money >= self.min_bet:
            content = QUESTION_HEADER_CHOICE + ",".join(choices)
            self.try_send_data(player, content)
            choice = self.try_receive_data(player)
        if player.player_money < self.min_bet or choice == choices[1] or choice == choices[2]:
            self.try_send_data(player,
                           f"{OUTPUT_HEADER}Thank you for playing. "
                           f"You left with ${player.player_money}")
            player.active = False
        if choice == choices[2]:
            player.connected = False
            self.try_send_data(player, DISCONNECT_MESSAGE)
            try:
                player.conn.close()
            except Exception:
                logging.error("There was an exception while trying to close the connection")

        self.refresh_player_lists()

    # Handles a normal ending of the game
    def game_end(self, choices):
        multipliers = [0] * len(self.active_players)
        dealer_sum = self.deck.sum_cards(self.dealer_cards)
        players_sum = [self.deck.sum_cards(player.player_cards) for player in self.active_players]
        choice_copy = copy.deepcopy(choices)
        values_to_append = ["Push", "Lost", "BlackJack", "Bust"]
        choice_copy = choice_copy + values_to_append
        for idx, player in enumerate(self.active_players):
            special = choice_copy.index(player.status)
            self.try_send_data(player,
                           f"{OUTPUT_HEADER}The dealer has {dealer_sum} points "
                           f"and the player has {players_sum[idx]} points!")
            if special == 4:
                multipliers[idx] = 0
            elif special == 5:
                multipliers[idx] = -1
            elif special == 6:
                multipliers[idx] = 2.5
            elif special == 3:
                self.try_send_data(player, f"{OUTPUT_HEADER}The player chose to surrender! They get half their bet back!")
                multipliers[idx] = -0.5
            elif players_sum[idx] > 21:
                self.try_send_data(player, f"{OUTPUT_HEADER}The player went bust! The player lost!")
                multipliers[idx] = -1
            elif dealer_sum > 21:
                self.try_send_data(player, f"{OUTPUT_HEADER}The dealer went bust! The player won!")
                multipliers[idx] = 1
            elif players_sum[idx] == dealer_sum:
                self.try_send_data(player,
                               f"{OUTPUT_HEADER}The player and dealer have the same number of points! A push occurred!")
                multipliers[idx] = 0
            elif players_sum[idx] > dealer_sum:
                self.try_send_data(player, f"{OUTPUT_HEADER}The player has more points than the dealer! The player won!")
                multipliers[idx] = 1
            elif players_sum[idx] < dealer_sum:
                self.try_send_data(player, f"{OUTPUT_HEADER}The player has less points than the dealer! The dealer won!")
                multipliers[idx] = -1

            if special == 2:
                multipliers[idx] *= 2

        return multipliers

    # Handles ending the game if someone got a blackjack
    def blackjack_check(self):

        dealer_sum = self.deck.sum_cards(self.dealer_cards)
        player_sum = [self.deck.sum_cards(player.player_cards) for player in self.active_players]

        for idx, player in enumerate(self.active_players):
            # returns the player multiplier by checking who the winner of the game is
            if player_sum[idx] == 21 and dealer_sum == 21:
                self.try_send_data(player, f"{OUTPUT_HEADER}The player and dealer both have a blackjack! A push occurred!")
                player.status = "Push"
            if dealer_sum == 21:
                self.try_send_data(player,
                               f"{OUTPUT_HEADER}The dealer has a blackjack! Any player who does not have a blackjack has instantly lost!")
                player.status = "Lost"
            if player_sum[idx] == 21:
                self.try_send_data(player,
                               f"{OUTPUT_HEADER}The player has a blackjack and the dealer does not! "
                               f"The player gets payed out 3 to 2!")
                player.status = "BlackJack"

    def broadcast(self, message_type, list=[]):
        if message_type == "score_board":
            # sorting players list according to thier final money amount
            self.players_list.sort(key=lambda x: x.player_money, reverse=True)

            name_and_money = [
                str(p) + ". " + self.players_list[p].name.ljust(10) + "$" + str(self.players_list[p].player_money) for p
                in range(len(self.players_list))]
            board_data = "SCORE BOARD".center(30) + "\n" + "\n".join(name_and_money) + "\n"

            broadcast_messsage = OUTPUT_HEADER + board_data

        elif message_type == "turn_action":
            logging.debug("Player status: " + str([player.status for player in self.active_players]))
            players_action = [player.name + " -> " + player.status for player in
                              self.active_players]
            players_cards = [player.name + " -> " + str(player.player_cards) for player in self.active_players]
            broadcast_messsage = OUTPUT_HEADER + "Players Turn Action\n" + "\n".join(players_action) + "\n"
            broadcast_messsage += "Player's Cards\n" + "\n".join(players_cards) + "\n"

        elif message_type == "continue_quit":
            players_action = []
            for player in list:
                if player in self.connected_players:
                    players_action.append(player.name + " -> " + "Stopped Betting")
                else:
                    players_action.append(player.name + " -> " + "Quit Game Completely (Or Disconnected)")

            broadcast_messsage = OUTPUT_HEADER + "\nPlayers who quit Game\n" + "\n".join(players_action) + "\n"

        elif message_type == "bet_amount":
            players_bet_amount = [player.name + " -> $" + str(list[idx]) for idx, player in enumerate(self.active_players)]
            broadcast_messsage = OUTPUT_HEADER + "\nPlayers Betting Money\n" + "\n".join(players_bet_amount) + "\n"

        for player in self.connected_players:
            self.try_send_data(player, broadcast_messsage)

    def try_send_data(self, player, msg):
        try:
            self.send_data(player, msg)
        except socket.error as e:
            print(f"An error occurred with the connection to {player.name} when attempting to send data. "
                  f"Dropping them from the list of connected players")
            player.connected = False
            self.refresh_player_lists()

    def send_data(self, player, msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        player.conn.sendall(send_length)
        player.conn.sendall(message)

    def try_receive_data(self, player):
        try:
            return self.receive_data(player)
        except socket.error as e:
            print(f"An error occurred with the connection to {player.name} when attempting to receive data. "
                  f"Dropping them from the list of connected players")
            player.connected = False
            self.refresh_player_lists()

            discmsg = OUTPUT_HEADER + f"{player.name} seems to have disconnected. " \
                                      f"There are now only {len(self.connected_players)} players"
            for rplayer in self.connected_players:
                self.try_send_data(rplayer, discmsg)

            return None

    def receive_data(self, player):
        msg_length = player.conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = player.conn.recv(msg_length).decode(FORMAT)
            return msg
        raise socket.error("Failed to receive data")
