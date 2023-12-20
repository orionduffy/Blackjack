import socket
import questionary
import logging
from utils import *

from colorama import Fore, Style


class Player:
    def __init__(self, name, server_ip):
        """This function initializes the Player object with Player info.
        
        Args:
            name (String): Player Name\n
            server_ip (string): the server ip address they want to connect\n
        """
        self.name = name
        self.SERVER = server_ip
        global HEADER
        global PORT
        ADDR = (self.SERVER, PORT)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(ADDR) 
        self.try_send_data(name)
        self.min_bet = 0
        self.player_money = 0

    def handle_requests(self):
        """This function handles the communicaton between the server and the \
            player and this either prints the data from the server to the screen \
            or get input from the user and send the data to the server."""
        while True:
            message = self.try_receive_data()
            if type(message) == int:
                print(f"{Fore.RED}An error has occurred on the server's end. Error code sent to player: {message}")
                print(f"Player Connection Closing...{Style.RESET_ALL}")
                self.client.close()
                break
            elif message.startswith(OUTPUT_HEADER):
                print(message[st:])
            elif message.startswith(QUESTION_HEADER_INPUT):
                choices = list(message[st:].split(','))
                self.player_money = int(choices[1])
                self.min_bet = int(choices[2])
                bet = questionary.text(choices[0], validate=self.validate_bet).ask()
                self.try_send_data(bet)
            elif message.startswith(QUESTION_HEADER_CHOICE):
                choices = list(message[st:].split(','))
                choice = questionary.select("What do you want to do?", choices=choices).ask()
                self.try_send_data(choice)
            elif message == DISCONNECT_MESSAGE:
                print(f"{Fore.GREEN}Player Connection Closing...{Style.RESET_ALL}")
                self.client.close()
                break

    def try_send_data(self, msg):
        """This function try to send data/msg using the send_data function to player and the exceptions are handled here.
    
        Args:
            msg (String): The message to be sent to the player \n
        
        Returns:
                boolean: True if succefully msg is sent, otherwise it return False
        """
        try:
            self.send_data(msg)
            return True
        except socket.error as e:
            logging.error(f"Error sending data to server: {e}")
            print(f"{Fore.RED}An error occurred with the server connection when attempting to send data. Closing Connection.{Style.RESET_ALL}")
            self.client.close()
            # return False

    def send_data(self, msg):
        """This function encode the msg and send it to a server conn
    
        Args:
            msg (String): The message to be sent to the player

        No Return.
        """

        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        self.client.sendall(send_length)
        self.client.sendall(message)

    def try_receive_data(self):
        """This function try to receive data/msg using the receive_data function from player and the exceptions are handled here.

        Returns:
               string: The data/msg received from the client or none if Failed to receive data
        """
        try:
            return self.receive_data()
        except socket.error as e:
            logging.error(f"Error receiving data from server: {e}")
            print(f"{Fore.RED}An error occurred with the server connection when attempting to receive data. Closing Connection.{Style.RESET_ALL}")
            self.client.close()
            # return None

    def receive_data(self):
        """This function receive data/msg from the server directed to the client.
        
        Args:

        Returns:
               string: The data/msg received from the client
        """
        msg_length = self.client.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = self.client.recv(msg_length).decode(FORMAT)
            return msg
        return 0

    def validate_bet(self, text):
        """This function validated the input data provided if it the player have sufficient amount for the bet.
    
        Args:
            text (String): input text

        Returns:
                boolean: True if text is enough amount for the bet else it return a string to notify bet is invalid.
        """
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
