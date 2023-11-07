import random
import questionary
from blackjack import Blackjack
from Player import Player
import re
import logging




# Runs a game of Blackjack
def main():
    print("Welcome to Blackjack!")

    player = Player("player_name", "172.19.93.54")
    player.Handle_requests()

    # game_type = ["Singleplayer", "Multiplayer"]
    # player_game_choice = questionary.select("What type of game do want to play?", choices=game_type).ask()

    # if player_game_choice == game_type[0]:
    #     blackjack = Blackjack()
    #     blackjack.run()
    # else:
    #     try:
    #         player_name = input("Enter your name? ")
    #         # server_ip = questionary.text("Please enter the Server IP you want to connect to?", validate_IP).ask()
    #         print(player_name)
    #         player = Player(player_name, "172.19.93.54")
    #         player.Handle_requests()
    #     except UserWarning as e:
    #         logging.error(f"UserWarning: {e}")
    #         print(f"Exception occurred: {e}")
    #     except Exception as e:
    #         logging.exception(f"Exception occurred: {e}")
    #         print(f"An unexpected error occurred. Please check the logs for details.")


def validate_IP(ip):
    # chatgpt
    ipv4_pattern = r"^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    if re.match(ipv4_pattern, ip):
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
