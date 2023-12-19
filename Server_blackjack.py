import questionary
from deck import Deck
import socket
import threading
import pdb
import copy
from Server_Player_Info import Player
from utils import *
import logging

# https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
from colorama import Fore, Style


# The main class for running the Blackjack game. Game will continue until the player either quits or runs out of money
class Blackjack:
    """This class is the Multiplayer Blackjack class hosted by the server."""

    def __init__(self, players):
        """
        This function initializes the Multiplayer Blackjack class with the list of Player objects.
        
        Args:
            players (list): List of Player objects waiting to play the game\n

        """
        self.min_bet: int = 5

        self.deck = Deck()
        self.shuffled_deck = self.deck.shuffle_deck()

        # The list of all players who have joined the game
        self.players_list = players
        # The list of players currently connected to the server
        self.connected_players = list(filter(lambda player: player.connected, self.players_list))
        # The list of players actively playing. Anyone who has chosen to stop betting is removed from this list
        self.active_players = list(filter(lambda player: player.connected and player.active, self.connected_players))

        self.dealer_cards = []
        self.bets = {}  # this will hold individual bets of every player

        logging.debug("Blackjack class initialized")

    def refresh_player_lists(self):
        """This function filters the players who are currently connected and those who want to continue playing."""
        self.connected_players = list(filter(lambda player: player.connected, self.players_list))
        # The active player list must always be filtered from the connected player list,
        # because disconnects might not change player.active to false.
        self.active_players = list(filter(lambda player: player.active, self.connected_players))

    # Runs the main game loop, which potentially includes several rounds
    def run(self):
        """
        This function get the betting amount from every player before every game \
        started and calls the run_round function to handle the action of every \
        player in every round. After single game is over, it adds or reduces the \
        won/loss amount to every player's money. The Game re-runs till the active players is 0.
        """
        self.refresh_player_lists()

        # def subFunction(self):
        self.bets = {player.name: 0 for player in self.active_players}

        # while self.players_money >= self.min_bet and choice == choices[0]:
        threads = []
        for player in self.active_players:
            if player.player_money >= self.min_bet:
                th = threading.Thread(target=self.thread1, args=(player,))
                threads.append(th)
                th.start()
        for th in threads: th.join()
        threads.clear()
        self.broadcast("bet_amount")

        multipliers = self.run_round()
        self.reset_game()

        win_or_loss_amt = {}

        for player in self.active_players:
            player.player_money += self.bets[player.name] * multipliers[player.name]
            win_or_loss_amt[player] = self.bets[player.name] * multipliers[player.name]
            player.player_money = int(player.player_money)
            self.try_send_data(player,
                               f"{OUTPUT_HEADER}{Fore.BLUE}You now have ${player.player_money}!{Style.RESET_ALL}")

        # Broadcasting the Score board after every game
        self.broadcast('score_board', win_or_loss_amt)

        # going for the next round and asking the player if they want to play or not
        for player in self.active_players:
            th = threading.Thread(target=self.thread3, args=(player,))
            threads.append(th)
            th.start()
        for th in threads: th.join()

        for player in self.players_list:
            if player.mid_join:
                player.rejoin_game()

        self.refresh_player_lists()

        self.broadcast("continue_quit")

        if len(self.active_players) > 0:
            self.run()

    # Runs the loop for an individual rounds,
    # which at a basic level involves drawing new cards until the player stops or goes over 21
    def run_round(self):
        """
        This function handles the actions of every players done after each round \
        and does the necessary action based on that.
        """
        for i in range(2):
            self.dealer_cards.append(self.shuffled_deck.pop(0))
            for player in self.active_players:
                player.player_cards.append(self.shuffled_deck.pop(0))

        for player in self.active_players:
            response = self.try_send_data(player,
                                          f"{OUTPUT_HEADER}{Fore.YELLOW}Dealer's up card{Style.RESET_ALL}: {self.dealer_cards[0]} "
                                          f"({self.deck.base_deck[self.dealer_cards[0]]} points)")
            if response:
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
            self.refresh_player_lists()
            # the flag indicate if the current game come to end and if True the while loop will terminate
            break_loop = [True]
            threads = []
            for player in self.active_players:
                if player.status == choices[0]:
                    th = threading.Thread(target=self.thread2, args=(player, first_round, choices))
                    threads.append(th)
                    th.start()
            for th in threads: th.join()
            self.refresh_player_lists()

            for player in self.active_players:
                if player.status == choices[0]:
                    player.player_cards.append(self.shuffled_deck.pop(0))

                    if self.deck.sum_cards(player.player_cards) > 21:
                        self.try_send_data(player, f"{OUTPUT_HEADER}{Fore.RED}You went Bust.\n{Style.RESET_ALL}")
                        player.status = "Bust"

                    if player.status == choices[0]:
                        break_loop[0] = False
                if player.status == choices[2] and first_round:
                    player.player_cards.append(self.shuffled_deck.pop(0))

            self.broadcast("turn_action")
            for player in self.active_players:
                self.print_player_info(player)

            if break_loop[0]:
                break
            first_round = False

        # if self.deck.sum_cards(self.players_cards) <= 21 and choice != choices[-1]:
        for player in self.connected_players:
            response = self.try_send_data(player, f"{OUTPUT_HEADER}The dealer now flips over their hole card.")
            if response:
                self.print_dealer_info(player)

        if self.deck.sum_cards(self.dealer_cards) < 17:
            while self.deck.sum_cards(self.dealer_cards) < 17:
                self.dealer_cards.append(self.shuffled_deck.pop(0))
            for player in self.active_players:
                response = self.try_send_data(player,
                                              f"{OUTPUT_HEADER}The dealer has less than 17 points. he begins drawing.")
                if response:
                    self.print_dealer_info(player)

        for player in self.active_players: self.try_send_data(player,
                                                              f"{OUTPUT_HEADER}{Fore.GREEN}Game over!{Style.RESET_ALL}")
        return self.game_end(choices)
        # else:
        #     # If one person has a blackjack, the game immediately ends
        #     self.try_send_data(f"{OUTPUT_HEADER}Game immediately over!")
        #     return self.blackjack_end()

    def reset_game(self):
        """This function resets some game variables before new game is started."""
        self.shuffled_deck = self.deck.shuffle_deck()

        for pl in self.players_list: pl.initialize_new_game()
        self.dealer_cards = []

    def print_player_info(self, player):
        """
        This function sends the player's current game info to the client.
        
        Args:
            player (Player): object of Player class

        Returns:
                boolean: True if sending the data was sucessful else False
        """
        response = self.try_send_data(player,
                                      f"{OUTPUT_HEADER}{Fore.YELLOW}Your cards{Style.RESET_ALL}: {player.player_cards} \n"
                                      f"{Fore.YELLOW}Player Sum{Style.RESET_ALL}: {self.deck.sum_cards(player.player_cards)}")
        return response

    def print_dealer_info(self, player):
        """
        This function sends the dealer's current game info to the client.
        
        Args:
            player (Player): object of Player class

        Returns:
                boolean: True if sending the data was successful else False
        """
        response = self.try_send_data(player,
                                      f"{OUTPUT_HEADER}{Fore.YELLOW}Dealer cards{Style.RESET_ALL}: {self.dealer_cards} \n"
                                      f"{Fore.YELLOW}Dealer sum{Style.RESET_ALL}: {self.deck.sum_cards(self.dealer_cards)}")
        return response

    # handles the process of getting bet amount from the players
    def thread1(self, player):
        """
        This function get the current game betting amount and handles the exception if error occurred.
        
        Args:
            player (Player): object of Player class

        Returns:
                boolean: True if getting the bettting amount was sucessful else False
        """
        response = self.try_send_data(player,
                                      f"{OUTPUT_HEADER}{Fore.BLUE}You have ${player.player_money} to bet with!{Style.RESET_ALL}")
        if not response:
            self.bets.pop(player.name)
            return False
        response = self.try_send_data(player,
                                      f"{QUESTION_HEADER_INPUT} How much would you like to bet?,"
                                      f"{player.player_money},{self.min_bet}")
        if not response:
            self.bets.pop(player.name)
            return False
        bet_attempt = self.try_receive_data(player)
        if not bet_attempt:
            self.bets.pop(player.name)
            return False
        else:
            try:
                self.bets[player.name] = int(bet_attempt)

                self.try_send_data(player,
                                   f"{OUTPUT_HEADER}{Fore.YELLOW}${self.bets[player.name]} will be bet! "
                                   f"You have ${player.player_money - self.bets[player.name]} left in reserve! \n"
                                   f"Game Beginning!\n{Style.RESET_ALL}")
            except ValueError:
                msg = f"{Fore.RED}Player {player.name}'s machine attempted to send an invalid input to the server.\n" \
                      f"There may be a bug, or the player may have modified the program.{Style.RESET_ALL}"
                logging.error(msg)
                print(msg)

    # handles the process of getting the player's turn choice and do the relevant action
    def thread2(self, player, first_round, choices):
        """
        This function get player's turn action of a round.
        
        Args:
            player (Player): object of Player class\n
            first_round (boolean): True if it is the first round of a game otherwise False\n
            choices (list): List of option a player can choose in every round.\n

        """
        if first_round:
            content = QUESTION_HEADER_CHOICE + ",".join(choices)
        else:
            content = QUESTION_HEADER_CHOICE + ",".join(choices[:-2])

        response = self.try_send_data(player, content)
        if not response:
            player.status = choices[1]
            return False
        received_data = self.try_receive_data(player)
        logging.debug(f"Turn choice received from {player.name}: {str(received_data)}")
        player.status = received_data if received_data else choices[1]

    # Handles if the player wants to continue or quit
    def thread3(self, player):
        """
        This function handles the player's action after the game is over and asks the player what they want to do next.
        
        Args:
            player (Player): object of Player class

        """
        choices = ["Continue", "Stop Betting", "Quit Game Completely"]
        choice = ""
        response = True
        if player.player_money >= self.min_bet:
            content = QUESTION_HEADER_CHOICE + ",".join(choices)
            response = self.try_send_data(player, content)
            if response:
                choice = self.try_receive_data(player)
            else:
                choice = None
        if player.player_money < self.min_bet or choice == choices[1] or choice == choices[2]:
            if response:
                response = self.try_send_data(player,
                                              f"{OUTPUT_HEADER}{Fore.BLUE}Thank you for playing. "
                                              f"You left with {Fore.GREEN}${player.player_money}{Style.RESET_ALL}")
            player.active = False
        if choice == choices[2]:
            player.connected = False
            if response:
                response = self.try_send_data(player, DISCONNECT_MESSAGE)
            try:
                player.conn.close()
            except Exception as error:
                logging.error(f"There was an exception while trying to close the connection: \n{error}")
        if choice is None:
            player.connected = False

        self.refresh_player_lists()

    # Handles a normal ending of the game
    def game_end(self, choices):
        """
        This function check if a player won/lost after the game is over \
        and calculates the multipliers amount for every player.
        
        Args:
            choices (list): List of option a player can choose in every round.

        Returns:
                list of int: multipliers to the betting amount
        """
        multipliers = {player.name: 0 for player in self.active_players}
        dealer_sum = self.deck.sum_cards(self.dealer_cards)
        players_sum = {player.name: self.deck.sum_cards(player.player_cards) for player in self.active_players}
        choice_copy = copy.deepcopy(choices)
        values_to_append = ["Push", "Lost", "BlackJack", "Bust"]
        choice_copy = choice_copy + values_to_append
        for player in self.active_players:
            special = choice_copy.index(player.status)
            self.try_send_data(player,
                               f"{OUTPUT_HEADER}The dealer has {dealer_sum} points "
                               f"and the player has {players_sum[player.name]} points!")
            if special == 4:
                multipliers[player.name] = 0
            elif special == 5:
                multipliers[player.name] = -1
            elif special == 6:
                multipliers[player.name] = 2.5
            elif special == 3:
                self.try_send_data(player,
                                   f"{OUTPUT_HEADER}{Fore.YELLOW}The player chose to surrender! They get half their bet back!{Style.RESET_ALL}")
                multipliers[player.name] = -0.5
            elif players_sum[player.name] > 21:
                self.try_send_data(player,
                                   f"{OUTPUT_HEADER}{Fore.RED}The player went bust! The player lost!{Style.RESET_ALL}")
                multipliers[player.name] = -1
            elif dealer_sum > 21:
                self.try_send_data(player,
                                   f"{OUTPUT_HEADER}{Fore.BLUE}The dealer went bust! The player won!{Style.RESET_ALL}")
                multipliers[player.name] = 1
            elif players_sum[player.name] == dealer_sum:
                self.try_send_data(player,
                                   f"{OUTPUT_HEADER}{Fore.YELLOW}The player and dealer have the same number of points! A push occurred!{Style.RESET_ALL}")
                multipliers[player.name] = 0
            elif players_sum[player.name] > dealer_sum:
                self.try_send_data(player,
                                   f"{OUTPUT_HEADER}{Fore.BLUE}The player has more points than the dealer! The player won!{Style.RESET_ALL}")
                multipliers[player.name] = 1
            elif players_sum[player.name] < dealer_sum:
                self.try_send_data(player,
                                   f"{OUTPUT_HEADER}{Fore.RED}The player has less points than the dealer! The dealer won!{Style.RESET_ALL}")
                multipliers[player.name] = -1

            if special == 2:
                multipliers[player.name] *= 2

        return multipliers

    # Handles ending the game if someone got a blackjack
    def blackjack_check(self):
        """This function checks if there is a blackjack win after the first two cards are given for every player."""
        dealer_sum = self.deck.sum_cards(self.dealer_cards)
        player_sum = [self.deck.sum_cards(player.player_cards) for player in self.active_players]

        for idx, player in enumerate(self.active_players):
            # returns the player multiplier by checking who the winner of the game is
            if player_sum[idx] == 21 and dealer_sum == 21:
                self.try_send_data(player,
                                   f"{OUTPUT_HEADER}{Fore.YELLOW}The player and dealer both have a blackjack! "
                                   f"A push occurred!{Style.RESET_ALL}")
                player.status = "Push"
            if dealer_sum == 21:
                self.try_send_data(player,
                                   f"{OUTPUT_HEADER}{Fore.RED}The dealer has a blackjack! "
                                   f"Any player who does not have a blackjack has instantly lost!{Style.RESET_ALL}")
                player.status = "Lost"
            if player_sum[idx] == 21:
                self.try_send_data(player,
                                   f"{OUTPUT_HEADER}{Fore.YELLOW}The player has a blackjack and the dealer does not! "
                                   f"The player gets payed out 3 to 2!{Style.RESET_ALL}")
                player.status = "BlackJack"

    def broadcast(self, message_type, win_or_loss_amt={}):
        """
        This function sends a broadcast message to all players.
        
        Args:
            message_type (String): one of these values ["score_board", "turn_action", "continue_quit", "bet_amount"]

        """
        def display_help(win_or_loss_amt, player):
            res = (str(win_or_loss_amt[player]) if player in win_or_loss_amt else "not playing").ljust(20)
            if res!="not playing         ":
                if int(res)>=0:
                    return f"{Fore.GREEN} +{res}{Style.RESET_ALL}"
                return f"{Fore.RED} {res}{Style.RESET_ALL}"
            return res

        if message_type == "score_board":
            # sorting players list according to thier final money amount
            self.players_list.sort(key=lambda x: x.player_money, reverse=True)

            name_and_money = [
                str(p + 1) + ". " + self.players_list[p].name.ljust(20) + "$" + \
                    str(self.players_list[p].player_money).ljust(20) + \
                    display_help(win_or_loss_amt, self.players_list[p])
                    
                for p
                in range(len(self.players_list))]

            board_data = "".rjust(30) + f"{Fore.GREEN}SCORE BOARD{Style.RESET_ALL}\n"
            board_data += "   Name".ljust(20) + "Total Money".ljust(20) + "Last Game win/loss Amt".center(20) + "\n"
            board_data += "\n".join(name_and_money) + "\n\n"


            broadcast_messsage = OUTPUT_HEADER + board_data

            win_or_loss_amt={}

        elif message_type == "turn_action":
            logging.debug("Player status: " + str([player.status for player in self.active_players]))
            players_action = [player.name + " -> " + player.status for player in
                              self.active_players]
            players_cards = [player.name + " -> " + str(player.player_cards) for player in self.active_players]
            broadcast_messsage = OUTPUT_HEADER + "".rjust(
                10) + f"{Fore.GREEN}Players Turn Action{Style.RESET_ALL}\n" + "\n".join(players_action) + "\n\n"
            broadcast_messsage += "".rjust(10) + f"{Fore.GREEN}Player's Cards{Style.RESET_ALL}\n" + "\n".join(
                players_cards) + "\n\n"

        elif message_type == "continue_quit":
            players_action = []
            quit_players = [player for player in self.players_list if
                            player not in self.active_players]

            if len(quit_players) == 0:
                return

            for player in quit_players:
                if player in self.connected_players:
                    players_action.append(player.name + " -> " + "Stopped Betting")
                else:
                    players_action.append(player.name + " -> " + "Quit Game Completely (Or Disconnected)")

            broadcast_messsage = OUTPUT_HEADER + "".rjust(
                10) + f"{Fore.GREEN}Players who quit Game{Style.RESET_ALL}\n" + "\n".join(players_action) + "\n"

        elif message_type == "bet_amount":
            players_bet_amount = [player.name + " -> $" + str(self.bets[player.name]) for player in self.active_players]
            broadcast_messsage = OUTPUT_HEADER + "".rjust(
                10) + f"{Fore.GREEN}Players Betting Money{Style.RESET_ALL}\n" + "\n".join(players_bet_amount) + "\n"

        for player in self.connected_players:
            self.try_send_data(player, broadcast_messsage)


    # send_data and receive_data can fail if the connection is broken.
    # try_send_data and try_receive_data exist to handle that, and should be used instead.
    # try_send_data and try_receive_data will remove the player from the active list
    # and return False or None if it fails, or the message or True if it succeeds
    # This way, you can simply end the thread if the response is not something that counts as true in an if statement
    def try_send_data(self, player, msg):
        """
        This function tries to send data/msg using the send_data function to player and the exceptions are handled here.
    
        Args:
            player (Player): Player object to which the msg is going to be delivered to\n
            msg (String): The message to be sent to the player\n
        
        Returns:
                boolean: True if msg is successfully sent, otherwise it returns False
        """
        try:
            send_data(player.conn, msg)
            return True
        except socket.error as e:
            logging.error(f"Error sending data to {player.name} at IP {player.address}: {e}")
            print(f"{Fore.RED}An error occurred with the connection to {player.name} when attempting to send data. "
                  f"Dropping them from the list of connected players{Style.RESET_ALL}")
            player.connected = False
            self.refresh_player_lists()

            discmsg = OUTPUT_HEADER + f"{Fore.RED}{player.name} seems to have disconnected. " \
                                      f"There are now only {len(self.connected_players)} players{Style.RESET_ALL}"
            for rplayer in self.connected_players:
                self.try_send_data(rplayer, discmsg)
            return False

    def try_receive_data(self, player):
        """
        This function tries to receive data or a message using the receive_data function \
        from the player and the exceptions are handled here.
    
        Args:
            player (Player): Player object to which the msg is going to be delivered to\n
        
        Returns:
               string: The data/msg received from the client or none if Failed to receive data
        """
        try:
            return receive_data(player.conn)
        except socket.error as e:
            logging.error(f"Error receiving data from {player.name} at Ip {player.address}: {e}")
            print(f"{Fore.RED}An error occurred with the connection to {player.name} when attempting to receive data. "
                  f"Dropping them from the list of connected players{Style.RESET_ALL}")
            player.connected = False
            self.refresh_player_lists()

            discmsg = OUTPUT_HEADER + f"{Fore.RED}{player.name} seems to have disconnected. " \
                                      f"There are now only {len(self.connected_players)} players{Style.RESET_ALL}"
            for rplayer in self.connected_players:
                self.try_send_data(rplayer, discmsg)

            return None
