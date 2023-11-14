import random
import questionary
from blackjack import Blackjack
from Player import Player
import re
import logging




# Runs a game of Blackjack
def main():
    print("Welcome to Blackjack!")

    # player = Player("player_name", "192.168.56.1")
    # player.Handle_requests()

    game_type = ["Singleplayer", "Multiplayer"]
    player_game_choice = questionary.select("What type of game do want to play?", choices=game_type).ask()

    if player_game_choice == game_type[0]:
        blackjack = Blackjack()
        blackjack.run()
    else:
        try:
            player_name = questionary.text("Enter Player name: ").ask()
            server_ip = questionary.text("Please enter the Server IP you want to connect to?", validate = validate_IP).ask()
            player = Player(player_name, server_ip)
            player.Handle_requests()
        except UserWarning as e:
            logging.error(f"UserWarning: {e}")
            print(f"Exception occurred: {e}")
        except Exception as e:
            logging.exception(f"Exception occurred: {e}")
            print(f"An unexpected error occurred. Please check the logs for details.")


def validate_IP(ip):
    
    ip_split = ip.split('.')
    if len(ip_split) == 4 and len(ip_split[3])>0 and int(ip_split[0]) >= 0 and int(ip_split[0]) <= 255 and int(ip_split[1]) >= 0 and int(ip_split[1]) <= 255 and int(ip_split[2]) >= 0 and int(ip_split[2]) <= 255 and int(ip_split[3]) >= 0 and int(ip_split[3]) <= 255:
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
