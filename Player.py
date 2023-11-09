import socket
import questionary
import logging


QUESTION_HEADER_CHOICE = "CHOOCE\n"
st = len(QUESTION_HEADER_CHOICE)
QUESTION_HEADER_INPUT = "IINPUT\n"
OUTPUT_HEADER = "OUTPUT\n"
DISCONNET_MESSAGE = "!DISCONNECT"

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
        self.sendData(name)
        self.min_bet = 0
        self.player_money = 0

    def Handle_requests(self):
        
        while True:
            message = self.receiveData()
            # print(message)
            if message.startswith(OUTPUT_HEADER):
                print(message[st:])
            elif message.startswith(QUESTION_HEADER_INPUT):
                Choices = list(message[st:].split(','))
                self.player_money= int(Choices[1])
                self.min_bet = int(Choices[2])
                bet = questionary.text(Choices[0], validate=self.validate_bet).ask()
                self.sendData(bet)
            elif message.startswith(QUESTION_HEADER_CHOICE):
                Choices = list(message[st:].split(','))
                choice = questionary.select("What do you want to do?", choices=Choices).ask()
                self.sendData(choice)
            elif message == DISCONNET_MESSAGE:
                print("Player Connection Closing...")
                client.close()
                break

    def sendData(self, msg):
        
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send(message)

    def receiveData(self):
        
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
                return "The minimum bet is $5"
            else:
                return True
        except ValueError:
            return "Please enter a number"
