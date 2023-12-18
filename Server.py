import questionary
from deck import Deck
import socket
import threading
import pdb
from Server_blackjack import Blackjack
from Server_Player_Info import Player
import logging
import multiprocessing
# The idea to use input timeouts was gained from professor Jamal Bouajjaj
from inputimeout import inputimeout, TimeoutOccurred

# https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
from colorama import init as colorama_init
from colorama import Fore, Style

# Much of the socket code is copied partly or fully from https://youtu.be/3QiPPX-KeSc?si=wLAnYlhsHv2Fuqry


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

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def handle_clients(players_list):
    blackjack = Blackjack(players_list)
    blackjack.run()
    connected_players = list(filter(lambda person: person.connected, players_list))
    for player in connected_players:
        send_data(player.conn, DISCONNECT_MESSAGE)
        player.conn.close()


def handle_late_connections(game_thread, players_list, allow_rejoins, allow_new_joins, hard_cap):
    # https://docs.python.org/3/library/socket.html#timeouts-and-the-accept-method
    server.settimeout(1)

    while game_thread.is_alive():
        try:
            conn, addr = server.accept()  # Accept a new connection
            base_name = receive_data(conn)
            if allow_rejoins:
                found_player = False
                for player in players_list:
                    if not player.connected and player.address == addr[0] and player.name[:-1] == base_name:
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
                pname = base_name + str(len(players_list))
                new_player = Player(pname, conn, addr, mid_join=True)
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
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    players_list = []
    no_players = int(questionary.text("How many players are you expecting?", validate=validate_no_players).ask())

    allow_rejoin = questionary \
        .confirm("Would you like to allow players to rejoin in between games if they disconnected?").ask()
    allow_new_joins = questionary \
        .confirm("Would you like to allow new players to join in between games?").ask()
    
    if allow_new_joins:
        hard_cap = questionary.confirm("Would you like to set a maximum number of players?").ask()
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
            pname = receive_data(conn) + str(len(players_list))

            new_player = Player(pname, conn, addr)
            print_above(f"Player {new_player.name} has joined")
            msg = OUTPUT_HEADER + f"{Fore.GREEN}{pname}, please wait for the game to start>>>>{Style.RESET_ALL}"

            send_data(conn, msg)
            players_list.append(new_player)
        except socket.error as e:
            print_above(f"{Fore.RED}An error occurred with the connection. "
                        f"Dropping them from the list of connected players{Style.RESET_ALL}")
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
        # else:
        #     early_thread = threading.Thread(target=early_start, args=(should_start,))
        #     early_thread.daemon = True
        #     early_thread.start()
    early_thread.join()
    start_game(players_list, allow_rejoin, allow_new_joins, hard_cap)


def early_start(should_start, players_list):
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
    pause_game = [False]
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
    try:
        send_data(player.conn, msg)
        return True
    except socket.error as e:
        msg = f"{Fore.RED}An error occurred with the connection to {player.name}. " \
              f"Dropping them from the list of connected players{Style.RESET_ALL}"
        if not pre_game:
            print(msg)
        else:
            print_above(msg)
        player.connected = False
        return False


def send_data(conn, msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    conn.sendall(send_length)
    conn.sendall(message)


def receive_data(conn):
    msg_length = conn.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
        return msg
    raise socket.error(f"{Fore.RED}Failed to receive data{Style.RESET_ALL}")


def validate_no_players(text):
    if text.isdigit():
        return True
    else:
        return "Invalid input. Please enter a valid number."


def print_above(msg, up_amount=1, newline_amount=1):
    """
    Based off https://stackoverflow.com/questions/73426135/python-how-to-print-to-the-console-while-typing-input
    Mostly copied from professor Jamal Bouajjaj

    This does the following codes, in order:
        - save cursor position
        - move cursor up one line at the start
        - scroll up terminal by 1
        - Add a new line (this command seems to be obscure?)
        - print the message
        - go back to saved position
    """
    print(f"\x1b[s\x1b[{up_amount}F\x1b[S\x1b[{newline_amount}L" + msg + "\x1b[u", end="", flush=True)


if __name__ == '__main__':
    try:
        logging.basicConfig(filename='blackjack_server.log', level=logging.DEBUG)
        print(f"{Fore.GREEN}[STARTING] server is starting...{Style.RESET_ALL}")
        start()
    except UserWarning as e:
        print(f"{Fore.RED}Exception occurred: {e}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Exception occurred: {e}{Style.RESET_ALL}")
        # TODO: Finish this
