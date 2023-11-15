import socket
import questionary
import logging


QUESTION_HEADER_CHOICE = "CHOOCE\n"
st = len(QUESTION_HEADER_CHOICE)
QUESTION_HEADER_INPUT = "IINPUT\n"
OUTPUT_HEADER = "OUTPUT\n"
DISCONNECT_MESSAGE = "!DISCONNECT"

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'

class Player:
    def __init__(self, name, server_ip):
        
        self.name = name
        self.SERVER = server_ip
        global HEADER
        global PORT
        ADDR = (self.SERVER, PORT)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(ADDR) 
        self.send_data(name)
        self.min_bet = 0
        self.player_money = 0

    def handle_requests(self):
        
        while True:
            message = self.receive_data()
            # print(message)
            if type(message) == int:
                print(f"An error has occurred on the server's end. Error code sent to player: {message}")
                print("Player Connection Closing...")
                self.client.close()
                break
            elif message.startswith(OUTPUT_HEADER):
                print(message[st:])
            elif message.startswith(QUESTION_HEADER_INPUT):
                choices = list(message[st:].split(','))
                self.player_money = int(choices[1])
                self.min_bet = int(choices[2])
                bet = questionary.text(choices[0], validate=self.validate_bet).ask()
                self.send_data(bet)
            elif message.startswith(QUESTION_HEADER_CHOICE):
                choices = list(message[st:].split(','))
                choice = questionary.select("What do you want to do?", choices=choices).ask()
                self.send_data(choice)
            elif message == DISCONNECT_MESSAGE:
                print("Player Connection Closing...")
                self.client.close()
                break

    def send_data(self, msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send(message)

    def receive_data(self):
        msg_length = self.client.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = self.client.recv(msg_length).decode(FORMAT)
            return msg
        return 0

    def validate_bet(self, text):
        try:
            bet = int(text)
            if bet > self.player_money:
                return "You don't have that much money! Please enter a lower amount"
            elif bet < self.min_bet:
                return f"The minimum bet is ${self.min_bet}"
            else:
                return True
        except ValueError:
            return "Please enter a number"
