import questionary
from deck import Deck
import socket
import threading
import pdb
from Server_blackjack import Blackjack
from Server_Player_Info import Player
import logging

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


def start():
    server.listen(3)
    print(f"[LISTENING] Server is listening on {SERVER}")
    players_list = []
    no_players = int(questionary.text("Please Enter number of players?", validate=validate_no_players).ask())
    print("Waiting for players to join...")

    while True:
        conn, addr = server.accept()
        try:
            pname = receive_data(conn) + str(len(players_list))
            newPlayer = Player(pname, conn)
            print(f"Player {newPlayer.name} has joined")
            msg = OUTPUT_HEADER + "Waiting to Start Game>>>>"
            send_data(conn, msg)
            players_list.append(newPlayer)
        except socket.error as e:
            print(f"An error occurred with the connection. "
                  f"Dropping them from the list of connected players")
            continue

        connected_players = list(filter(lambda person: person.connected, players_list))
        print(f"There are now {len(connected_players)} players")

        lobbymsg = OUTPUT_HEADER + f"{newPlayer.name} has joined the lobby. " \
                                   f"There are now {len(connected_players)} players"
        dropped_players = False
        for player in connected_players:
            connect = try_send_data(player, lobbymsg)
            if not connect:
                dropped_players = True

        if dropped_players:
            connected_players = list(filter(lambda person: person.connected, players_list))
            discmsg = OUTPUT_HEADER + f"One or more players disconnected. " \
                                      f"There are now only {len(connected_players)} players"
            for player in connected_players:
                try_send_data(player, discmsg)

        if len(connected_players) == no_players:
            thread = threading.Thread(target=handle_clients, args=(players_list,))
            print("Game Starting ....")
            thread.start()
            thread.join()
            print("Game End...Server Shutting down")
            break

def try_send_data(player, msg):
    try:
        send_data(player.conn, msg)
        return True
    except socket.error as e:
        print(f"An error occurred with the connection to {player.name}. "
              f"Dropping them from the list of connected players")
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
        print("[STARTING] server is starting...")
        start()
    except UserWarning as e:
        print(f"Exception occurred: {e}")
    except Exception as e:
        print(f"Exception occurred: {e}")
        # TODO: Finish this

# def start():
#     server.listen()
#     print(f"[LISTENING] Server is listening on {SERVER}")
#     list_of_players = []
#     while True:
#         conn, addr = server.accept()
#         thread = threading.Thread(target = handle_client, args=(conn,addr))
#         thread.start()
#         print(f"[ACTIVE CONNECTIONS] {threading.activeCount()-1}")
