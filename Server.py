import questionary
from deck import Deck
import socket
import threading
import pdb
from Server_blackjack import Blackjack
from Server_Player_Info import Player
import logging

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


def handle_late_connections(server, game_thread):
    # https://docs.python.org/3/library/socket.html#timeouts-and-the-accept-method
    server.settimeout(1) 

    while game_thread.is_alive():
        try:
            conn, addr = server.accept()  # Accept a new connection
            send_data(conn, f"{OUTPUT_HEADER}Game has started without you. You can't join the game now. Try again later!!")
            send_data(conn, DISCONNECT_MESSAGE)
        except socket.timeout:
            pass  


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    players_list = []
    no_players = int(questionary.text("Please Enter number of players?", validate=validate_no_players).ask())
    print(f"{Fore.GREEN}Waiting for players to join...{Style.RESET_ALL}")

    while True:
        conn, addr = server.accept()
        
        try:
            pname = receive_data(conn) + str(len(players_list))
            newPlayer = Player(pname, conn)
            print(f"Player {newPlayer.name} has joined")
            msg = OUTPUT_HEADER + F"{Fore.GREEN}{pname} please wait for the Game to start>>>>{Style.RESET_ALL}"
            send_data(conn, msg)
            players_list.append(newPlayer)
        except socket.error as e:
            print(f"{Fore.RED}An error occurred with the connection. "
                  f"Dropping them from the list of connected players{Style.RESET_ALL}")
            continue

        connected_players = list(filter(lambda person: person.connected, players_list))
        print(f"{Fore.BLUE}There are now {len(connected_players)} players{Style.RESET_ALL}")

        lobbymsg = OUTPUT_HEADER + f"{Fore.BLUE}{newPlayer.name} has joined the lobby. " \
                                   f"There are now {len(connected_players)} players. Waiting for {no_players - len(connected_players)} more players to join.{Style.RESET_ALL}"
        dropped_players = False
        for player in connected_players:
            connect = try_send_data(player, lobbymsg)
            if not connect:
                dropped_players = True

        if dropped_players:
            connected_players = list(filter(lambda person: person.connected, players_list))
            discmsg = OUTPUT_HEADER + f"{Fore.RED}One or more players disconnected. {Style.RESET_ALL}" \
                                      f"{Fore.BLUE}There are now only {len(connected_players)} players. Waiting for {no_players - len(connected_players)} more players to join.{Style.RESET_ALL}"
            for player in connected_players:
                try_send_data(player, discmsg)

        if len(connected_players) == no_players:
            thread = threading.Thread(target=handle_clients, args=(players_list,))
            thread_reject = threading.Thread(target=handle_late_connections, args=(server,thread))
            print(f"{Fore.GREEN}Game Starting ....{Style.RESET_ALL}")
            thread.start()
            thread_reject.start()
            thread.join()
            thread_reject.join()
            print(f"{Fore.GREEN}Game End...Server Shutting down{Style.RESET_ALL}")
            break

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

