import questionary
from deck import Deck
import socket
import threading
import pdb
from Server_blackjack import Blackjack
from Server_Player_Info import Player
import logging
import multiprocessing

# https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
from colorama import init as colorama_init
from colorama import Fore,Style

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


def handle_late_connections(game_thread, players_list, allow_rejoins, allow_new_joins):
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
                        send_data(conn,
                                  f"{OUTPUT_HEADER}You have successfully reconnected "
                                  f"and will keep your previous progress, "
                                  f"but the game has already started. "
                                  f"You will have to wait until the next round starts to play!")
                        break

                if found_player:
                    continue

            if allow_new_joins:
                pname = base_name + str(len(players_list))
                new_player = Player(pname, conn, addr, mid_join=True)
                players_list.append(new_player)

                print(f"Player {new_player.name} at IP {new_player.address} has just joined the game")
                send_data(conn,
                          f"{OUTPUT_HEADER}You have successfully connected, "
                          f"but the game has already started. "
                          f"You will have to wait until the next round starts to play!")
            elif allow_rejoins:
                send_data(conn,
                          f"{OUTPUT_HEADER}Game has started without you. "
                          f"New players are not allowed to join. "
                          f"Try again later!!")
                send_data(conn, DISCONNECT_MESSAGE)
            else:
                send_data(conn,
                          f"{OUTPUT_HEADER}Game has started without you. "
                          f"You can't join the game now. "
                          f"Try again later!!")
                send_data(conn, DISCONNECT_MESSAGE)
        except socket.timeout:
            pass


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    players_list = []
    no_players = int(questionary.text("Please enter number of players:", validate=validate_no_players).ask())

    allow_rejoin = questionary \
        .confirm("Would you like to allow players to rejoin in between games if they disconnected?").ask()
    allow_new_joins = questionary \
        .confirm("Would you like to allow new players to join in between games?").ask()

    print(f"{Fore.GREEN}Waiting for players to join...{Style.RESET_ALL}")

    should_start = [False]

    while not should_start[0]:
        server.settimeout(1)
        try:
            conn, addr = server.accept()
        except socket.timeout:
            continue

        try:
            pname = receive_data(conn) + str(len(players_list))
            
            newPlayer = Player(pname, conn, addr)
            print(f"Player {newPlayer.name} has joined")
            msg = OUTPUT_HEADER + F"{Fore.GREEN}{pname} please wait for the Game to start>>>>{Style.RESET_ALL}"
            
            send_data(conn, msg)
            players_list.append(new_player)
        except socket.error as e:
            print(f"{Fore.RED}An error occurred with the connection. "
                  f"Dropping them from the list of connected players{Style.RESET_ALL}")
            continue

        connected_players = list(filter(lambda person: person.connected, players_list))
        print(f"{Fore.BLUE}There are now {len(connected_players)} players{Style.RESET_ALL}")

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
            should_start[0] = True
        # else:
        #     early_thread = threading.Thread(target=early_start, args=(should_start,))
        #     early_thread.daemon = True
        #     early_thread.start()

    start_game(players_list, allow_rejoin, allow_new_joins)


def early_start(should_start):
    should_start[0] = questionary \
        .confirm("Would you like to start the game early? "
                 "Note: A response to this question is not needed if the answer is not \"Yes\"").ask()


def start_game(players_list, allow_rejoin, allow_new_joins):
    pause_game = [False]
    thread = threading.Thread(target=handle_clients, args=(players_list,))
    thread_reject = threading.Thread(target=handle_late_connections, args=(thread,
                                                                           players_list,
                                                                           allow_rejoin,
                                                                           allow_new_joins))
    print(f"{Fore.GREEN}Game Starting ....{Style.RESET_ALL}")
    thread.start()
    thread_reject.start()
    thread.join()
    thread_reject.join()
    print(f"{Fore.GREEN}Game End...Server Shutting down{Style.RESET_ALL}")


def try_send_data(player, msg):
    try:
        send_data(player.conn, msg)
        return True
    except socket.error as e:
        print(f"{Fore.RED}An error occurred with the connection to {player.name}. "
              f"Dropping them from the list of connected players{Style.RESET_ALL}")
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
    raise socket.error("Failed to receive data")


def validate_no_players(text):
    if text.isdigit():
        return True
    else:
        return "Invalid input. Please enter a valid number."


if __name__ == '__main__':
    try:
        logging.basicConfig(filename='blackjack_server.log', level=logging.DEBUG)
        print(f"{Fore.GREEN}[STARTING] server is starting...{Style.RESET_ALL}")
        start()
    except UserWarning as e:
        print(f"Exception occurred: {e}")
    except Exception as e:
        print(f"Exception occurred: {e}")
        # TODO: Finish this
