import socket
import questionary

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
QUESTION_HEADER_CHOICE = "CHOOCE\n"
st = len(QUESTION_HEADER_CHOICE)
QUESTION_HEADER_INPUT = "IINPUT\n"
OUTPUT_HEADER = "OUTPUT\n"
DISCONNET_MESSAGE = "!DISCONNECT"
SERVER = "172.19.93.54"
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR) 
min_bet = 0
player_money = 0

def Handle_requests():
    while True:
        global min_bet
        global player_money
        message = receive()
        # print(message)
        if message.startswith(OUTPUT_HEADER):
            print(message[st:])
        elif message.startswith(QUESTION_HEADER_INPUT):
           Choices = list(message[st:].split(','))
           player_money= int(Choices[1])
           min_bet = int(Choices[2])
           bet = questionary.text(Choices[0], validate=validate_bet).ask()
           send(bet)
        elif message.startswith(QUESTION_HEADER_CHOICE):
            Choices = list(message[st:].split(','))
            choice = questionary.select("What do you want to do?", choices=Choices).ask()
            send(choice)
        elif message == DISCONNET_MESSAGE:
            print("Player Connection Closing...")
            client.close()
            break



def send(msg):
    global HEADER
    global FORMAT
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)

def receive():
    global HEADER
    global FORMAT
    msg_length = client.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = client.recv(msg_length).decode(FORMAT)
        return msg
    return 0

def validate_bet(text):
        try:
            bet = int(text)
            if bet > player_money:
                return "You don't have that much money! Please enter a lower amount"
            elif bet < min_bet:
                return "The minimum bet is $5"
            else:
                return True
        except ValueError:
            return "Please enter a number"

print("Player joined the game.")
Handle_requests()

