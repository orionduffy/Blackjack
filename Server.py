import questionary
import socket
import threading
from Server_blackjack import Blackjack
from Server_Player_Info import Player
from utils import *
import logging
# The idea to use input timeouts was gained from professor Jamal Bouajjaj
from inputimeout import inputimeout, TimeoutOccurred

# https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
from colorama import init as colorama_init
from colorama import Fore, Style


def handle_clients(players_list):
    """""
    This function starts the Blackjack game with the list of players \
    and gracefully closes the connection of players after the game is over.

    Args:
        players_list (list): List of Player objects which reprsents every players
    
    """
    blackjack = Blackjack(players_list)
    blackjack.run()
    connected_players = list(filter(lambda person: person.connected, players_list))
    for player in connected_players:
        send_data(player.conn, DISCONNECT_MESSAGE)
        player.conn.close()


def handle_late_connections(game_thread, players_list, allow_rejoins, allow_new_joins, hard_cap):
    """
    This function handles players who joined the lobby after the blackjack game is started.
    
    Args:
        game_thread (Thread): Current thread of the ongoing game\n
        players_list (list): List of Player objects playing the current game\n
        allow_rejoins (boolean): True if rejoins are allowed after player got disconneted for any reason otherwise False\n
        allow_new_joins (boolean): True if new players are allowed to join the game after it has started otherwise False\n
        hard_cap (int | boolean): The maximum number of players allowed, or False if there is no hard cap\n

    No Returns:

    """
    
    # https://docs.python.org/3/library/socket.html#timeouts-and-the-accept-method
    server.settimeout(1)

    while game_thread.is_alive():
        try:
            conn, addr = server.accept()  # Accept a new connection
            base_name = receive_data(conn)
            if allow_rejoins:
                found_player = False
                for player in players_list:
                    if not player.connected and player.address == addr[0] and player.pname == base_name:
                        player.handle_mid_join(conn)
                        found_player = True

                        print(f"Player {player.name} at IP {player.address} has rejoined the game")
                        try_send_data(player,
                                      f"{OUTPUT_HEADER}{Fore.GREEN}You have successfully reconnected "
                                      f"and will keep your previous progress, "
                                      f"but the game has already started. "
                                      f"You will have to wait until the next round starts to play!{Style.RESET_ALL}")
                        break

                """
                If the player has been found and had their "account" reactivated, 
                then there is no need to handle a new player joining or them getting rejected,
                so we skip to the next connection
                """
                if found_player:
                    continue

            # This section handles new players trying to join or a rejected connection
            # Players are allowed to rejoin if the hard cap has been met, but no new players are allowed to join
            if hard_cap and len(players_list) >= hard_cap:
                send_data(conn,
                          f"{OUTPUT_HEADER}{Fore.RED}The game has started without you, "
                          f"and the maximum number of players has been reached. "
                          f"Try again later!!{Style.RESET_ALL}")
                send_data(conn, DISCONNECT_MESSAGE)
            elif allow_new_joins:
                new_player = Player(base_name, len(players_list), conn, addr, mid_join=True)
                players_list.append(new_player)

                print(f"Player {new_player.name} at IP {new_player.address} has just joined the game")
                try_send_data(new_player,
                              f"{OUTPUT_HEADER}{Fore.GREEN}You have successfully connected, "
                              f"but the game has already started. "
                              f"You will have to wait until the next round starts to play!{Style.RESET_ALL}")
            elif allow_rejoins:
                send_data(conn,
                          f"{OUTPUT_HEADER}{Fore.RED}The game has started without you, "
                          f"and new players are not allowed to join. "
                          f"Try again later!!{Style.RESET_ALL}")
                send_data(conn, DISCONNECT_MESSAGE)
            else:
                send_data(conn,
                          f"{OUTPUT_HEADER}{Fore.RED}The game has started without you, "
                          f"and you can't join the game now. "
                          f"Try again later!!{Style.RESET_ALL}")
                send_data(conn, DISCONNECT_MESSAGE)
        except socket.timeout:
            pass


def start():
    """
    This function initiates the server to listen and after players are joined,
    it calls the start_game function to start game. \
    early_start function is also called in here if the early start of the game is needed.
    """
    server.bind(ADDR)
    # Suggested by professor
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.listen()
    print(f"[LISTENING] Server is listening on all available addresses")
    print(f"Players on the same computer can connect using localhost or 127.0.0.1")
    print(f"Players on the same network can connect using {socket.gethostbyname(socket.gethostname())}")
    print(f"Players on other networks can connect using the ip given by searching \"what is my ip\" on Google")

    players_list = []
    no_players = int(questionary.text("How many players are you expecting?", validate=validate_no_players).ask())

    allow_rejoin = questionary \
        .confirm("Would you like to allow players to rejoin in between games if they disconnected?").ask()
    allow_new_joins = questionary \
        .confirm("Would you like to allow new players to join in between games?").ask()

    if allow_new_joins:
        hard_cap = questionary.confirm("Would you like to set a maximum number of players?").ask()
    else:
        hard_cap = False

    if hard_cap:
        hard_cap = questionary.text("What is the maximum number of players you want to allow to join your game?",
                                    validate=validate_no_players).ask()
        hard_cap = int(hard_cap)

    print(f"{Fore.GREEN}Waiting for players to join...{Style.RESET_ALL}")

    should_start = [False]

    early_thread = threading.Thread(target=early_start, args=(should_start, players_list))
    early_thread.daemon = True
    early_thread.start()

    while not should_start[0]:
        server.settimeout(1)
        try:
            conn, addr = server.accept()
        except socket.timeout:
            continue

        try:
            pname = receive_data(conn)

            new_player = Player(pname, len(players_list), conn, addr)
            print_above(f"Player {new_player.name} has joined")
            msg = OUTPUT_HEADER + f"{Fore.GREEN}{pname}, please wait for the game to start>>>>{Style.RESET_ALL}"

            send_data(conn, msg)
            players_list.append(new_player)
        except socket.error as error:
            print_above(f"{Fore.RED}An error occurred with the connection. "
                        f"Dropping them from the list of connected players{Style.RESET_ALL}")
            logging.debug(f"Socket error when handling connection to potential new player: {error}")
            continue

        connected_players = list(filter(lambda person: person.connected, players_list))
        print_above(f"{Fore.BLUE}There are now {len(connected_players)} players{Style.RESET_ALL}")

        lobbymsg = OUTPUT_HEADER + f"{Fore.BLUE}{new_player.name} has joined the lobby. " \
                                   f"There are now {len(connected_players)} players. " \
                                   f"Waiting for {no_players - len(connected_players)} more players to join.{Style.RESET_ALL}"

        dropped_players = False
        for player in connected_players:
            connect = try_send_data(player, lobbymsg)
            if not connect:
                dropped_players = True

        if dropped_players:
            connected_players = list(filter(lambda person: person.connected, players_list))

            discmsg = OUTPUT_HEADER + f"{Fore.RED}One or more players disconnected. {Style.RESET_ALL}" \
                                      f"{Fore.BLUE}There are now only {len(connected_players)} players. " \
                                      f"Waiting for {no_players - len(connected_players)} more players to join.{Style.RESET_ALL}"

            for player in connected_players:
                try_send_data(player, discmsg)

        if len(connected_players) == no_players:
            connected_players = list(filter(lambda person: person.connected, players_list))
            alert = OUTPUT_HEADER + f"{Fore.GREEN}The lobby is full. " \
                                    f"The game is starting with {len(connected_players)} players.{Style.RESET_ALL}"

            for player in connected_players:
                try_send_data(player, alert)

            should_start[0] = True
    early_thread.join()
    start_game(players_list, allow_rejoin, allow_new_joins, hard_cap)


def early_start(should_start, players_list):
    """
    This function gives the ability to start the game early if needed by the server.

    Args:
        should_start (list[boolean]): True if the game is need to start early, otherwise False\n
        players_list (list): List of Player objects waiting to the game start_game\n

    No Return:
    """
    # should_start[0] = questionary \
    #     .confirm("Would you like to start the game early? "
    #              "Note: A response to this question is not needed if the answer is not \"Yes\"").ask()
    msg = "Press the enter key at any time to start the game early. "

    try:
        inputimeout(msg, timeout=1)
    except TimeoutOccurred:
        pass

    while not should_start[0]:
        try:
            inputimeout(f"\x1b[1F{msg}", timeout=1)
        except TimeoutOccurred:
            continue

        if not should_start[0]:
            connected_list = list(filter(lambda person: person.connected, players_list))
            alert = OUTPUT_HEADER + f"{Fore.GREEN}The game is starting early. " \
                                    f"There are {len(connected_list)} players participating.{Style.RESET_ALL}"

            for player in connected_list:
                try_send_data(player, alert)

            should_start[0] = True


def start_game(players_list, allow_rejoin, allow_new_joins, hard_cap):
    """
    This function start the handle_clients and handle_late_connections threads \
    and shuts down the server after the game is over and the players are gracefully disconnected.

    Args:
        players_list (list): List of Player objects waiting for the game to start\n
        allow_rejoin (boolean): True if rejoins are allowed after player got disconnected for any reason otherwise False\n
        allow_new_joins (boolean): True if new players are allowed to join the game after it has started otherwise False\n
        hard_cap (int | boolean): The maximum number of players allowed, or False if there is no hard cap\n

    No Return
    """
    thread = threading.Thread(target=handle_clients, args=(players_list,))
    thread_late_conn = threading.Thread(target=handle_late_connections,
                                        args=(thread, players_list, allow_rejoin, allow_new_joins, hard_cap))

    print(f"{Fore.GREEN}Game Starting ....{Style.RESET_ALL}")

    thread.start()
    thread_late_conn.start()
    thread.join()
    thread_late_conn.join()

    print(f"{Fore.GREEN}Game End...Server Shutting down{Style.RESET_ALL}")


def try_send_data(player, msg, pre_game=False):
    """
    This function try to send data using the send_data function to player and the exceptions are handled here.

    Args:
        player (Player): Player object to which the msg is going to be delivered\n
        msg (String): The message to be sent to the player\n
        pre_game (boolean): used to specify the msg print position on the server terminal\n

    Returns:
            boolean: True if msg is successfully sent, otherwise it returns False
    """
    try:
        send_data(player.conn, msg)
        return True
    except socket.error as error:
        msg = f"{Fore.RED}An error occurred with the connection to {player.name}. " \
              f"Dropping them from the list of connected players{Style.RESET_ALL}"
        logging.debug(f"Error occurred with the connection to {player.name} at IP {player.address}: {error}")
        if not pre_game:
            print(msg)
        else:
            print_above(msg)
        player.connected = False
        return False


def validate_no_players(text):
    """
    This function validated the input data provided if it a number.
    
    Args:
        text (String): input text

    Returns:
            boolean: True if text is digit else it return a string to notify text is not string.
    """
    try:
        int(text)
        return True
    except ValueError:
        return "Invalid input. Please enter a valid number."


if __name__ == '__main__':
    try:
        logging.basicConfig(filename='blackjack_server.log', level=logging.DEBUG)
        print(f"{Fore.GREEN}[STARTING] server is starting...{Style.RESET_ALL}")
        start()
    except UserWarning as e:
        print(f"{Fore.RED}Exception occurred: {e}{Style.RESET_ALL}")
        logging.error(e)
    except Exception as e:
        print(f"{Fore.RED}Exception occurred: {e}{Style.RESET_ALL}")
        logging.error(e)
