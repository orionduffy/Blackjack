import questionary
from deck import Deck
import socket
import threading
import pdb
from Server_blackjack import Blackjack


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

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def handle_clients(list_of_players):
    while True:
        blackjack = Blackjack(list_of_players)
        blackjack.run()
        # blackjack.sendData(DISCONNET_MESSAGE)
        # conn.close()


def start():
    server.listen(3)
    print(f"[LISTENING] Server is listening on {SERVER}")
    list_of_players = []
    while True:
        conn, addr = server.accept()
        list_of_players.append(conn)
        print(f"[ACTIVE CONNECTIONS] {list_of_players}")
        if len(list_of_players) == 2:
            thread = threading.Thread(target = handle_clients, args=(list_of_players,))
            thread.start()
            list_of_players = []
        

print("[STARTING] server is starting...")
start()


# def start():
#     server.listen()
#     print(f"[LISTENING] Server is listening on {SERVER}")
#     list_of_players = []
#     while True:
#         conn, addr = server.accept()
#         thread = threading.Thread(target = handle_client, args=(conn,addr))
#         thread.start()
#         print(f"[ACTIVE CONNECTIONS] {threading.activeCount()-1}")