import random
import socket

import questionary
from blackjack import Blackjack
from Player import Player
from utils import *
import re
import logging

# https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
from colorama import Fore, Style


# Runs a game of Blackjack
def main():
    print(f"{Fore.GREEN}Welcome to Blackjack!{Style.RESET_ALL}")

    game_type = ["Singleplayer", "Multiplayer"]
    player_game_choice = questionary.select("What type of game do want to play?", choices=game_type).ask()

    if player_game_choice == game_type[0]:
        blackjack = Blackjack()
        blackjack.run()
    else:
        try:
            player_name = questionary.text("Enter Player name: ").ask()
            server_ip = questionary.text("Please enter the Server IP you want to connect to?",
                                         validate=validate_IP).ask().strip()
            player = Player(player_name, server_ip)
            player.handle_requests()
        except UserWarning as e:
            logging.error(f"{Fore.RED}UserWarning: {e}{Style.RESET_ALL}")
            print(f"{Fore.RED}Exception occurred: {e}{Style.RESET_ALL}")
        except ConnectionRefusedError as e:
            logging.exception(f"{Fore.RED}ConnectionRefusedError: {e}{Style.RESET_ALL}")
            print(f"{Fore.RED}The connection was refused by the server. "
                  f"The server may be down, or the port may not be forwarded{Style.RESET_ALL}")
        except ConnectionResetError as e:
            logging.exception(f"{Fore.RED}ConnectionResetError: {e}{Style.RESET_ALL}")
            print(f"{Fore.RED}The connection was reset. "
                  f"The server may have gone down, or you may have lost internet connection{Style.RESET_ALL}")
        except socket.error as e:
            logging.exception(f"{Fore.RED}Socket error: {e}{Style.RESET_ALL}")
            print(f"{Fore.RED}An error occurred with the socket connection. Error: {e}{Style.RESET_ALL}")
        except Exception as e:
            logging.exception(f"{Fore.RED}Exception occurred: {e}{Style.RESET_ALL}")
            print(f"{Fore.RED}An unexpected error occurred. Error: {e}{Style.RESET_ALL}")


def validate_IP(ip):
    """
    This function checks if the input text is a valid ip address.
    
     Args:
          ip (String): input text

    Returns:
            boolean: True if input ip is valid else it return a string to notify input ip is not valid.
    """
    if len(ip) > 0:
        ip.strip()
    if ip == "localhost":
        return True
    ip_split = ip.split('.')
    if len(ip_split) == 4 and len(ip_split[0]) > 0 \
            and len(ip_split[1]) > 0 \
            and len(ip_split[2]) > 0 \
            and len(ip_split[3]) > 0 \
            and 0 <= int(ip_split[0]) <= 255 \
            and 0 <= int(ip_split[1]) <= 255 \
            and 0 <= int(ip_split[2]) <= 255 \
            and 0 <= int(ip_split[3]) <= 255:
        return True
    else:
        return "Please Enter Valid IP Server Address"


if __name__ == '__main__':
    try:
        logging.basicConfig(filename='blackjack.log', level=logging.DEBUG)
        main()
    except UserWarning as e:
        print(f"Exception occurred: {e}")
    except Exception as e:
        print(f"Exception occurred: {e}")
        # TODO: Finish this
