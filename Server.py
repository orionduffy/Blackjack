import questionary
from deck import Deck
import socket
import threading
import pdb
from Server_blackjack import Blackjack
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
    players_list = []
    no_players = int(questionary.text("Please Enter number of players?", validate = validate_no_players).ask())

    while True:
        conn, addr = server.accept()
        pname = receiveData(conn) + str(len(players_list))
        newPlayer = Player(pname, conn)
        msg = OUTPUT_HEADER + "Waiting to Start Game>>>>"
        sendData(conn, msg)
        players_list.append(newPlayer)
        if len(players_list) == no_players:
            thread = threading.Thread(target = handle_clients, args=(players_list,))
            print("Game Starting ....")
            thread.start()
            thread.join()
            print("Game End...Server Shutting down")
            break
        

def sendData(conn, msg):
    
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    conn.send(send_length)
    conn.send(message)

def receiveData(conn):

    msg_length = conn.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
        return msg
    return 0

def validate_no_players(text):
    if text.isdigit():
        return True 
    else:
        return "Invalid input. Please enter a valid number."

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

