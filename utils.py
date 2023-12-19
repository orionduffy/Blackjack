# https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
from colorama import init as colorama_init
from colorama import Fore, Style
import socket

# Much of the socket code is copied partly or fully from https://youtu.be/3QiPPX-KeSc?si=wLAnYlhsHv2Fuqry
HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
QUESTION_HEADER_CHOICE = "CHOOCE\n"
QUESTION_HEADER_INPUT = "IINPUT\n"
OUTPUT_HEADER = "OUTPUT\n"


PORT = 5050
# SERVER = "172.19.93.54"
# SERVER = socket.gethostbyname(socket.gethostname())
SERVER = ""
ADDR = (SERVER, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

colorama_init()


def print_above(msg, up_amount=1, newline_amount=1):
    """
    Based off https://stackoverflow.com/questions/73426135/python-how-to-print-to-the-console-while-typing-input \n
    Mostly copied from professor Jamal Bouajjaj

    This does the following things, in order:
        - save cursor position
        - move cursor up one line at the start
        - scroll up terminal by 1
        - Add a new line (this command seems to be obscure?)
        - print the message
        - go back to saved position

    Args:
        msg (String): The message that needs to be printed
        up_amount (int): The number of lines to move the cursor upwards
        newline_amount (int): The number of newlines to add

    No Return.
    """
    print(f"\x1b[s\x1b[{up_amount}F\x1b[S\x1b[{newline_amount}L" + msg + "\x1b[u", end="", flush=True)


def send_data(conn, msg):
    """
    This function encodes the msg and sends it to a player's conn information

    Args:
        conn (Socket): socket object usable to send and receive data/msg\n
        msg (String): The message to be sent to the player\n

    No Return.
    """
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    conn.sendall(send_length)
    conn.sendall(message)


def receive_data(conn):
    """
    This function receive data/msg from the clients directed to the server.

    Args:
        conn (Socket): socket object usable to send and receive data/msg

    Returns:
        string: The data/msg received from the client or raises an error if Failed to receive data
    """
    msg_length = conn.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
        return msg
    raise socket.error(f"{Fore.RED}Failed to receive data{Style.RESET_ALL}")