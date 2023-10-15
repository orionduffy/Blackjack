import random
import questionary
from blackjack import Blackjack



# Runs a game of Blackjack
def main():
    print("Welcome to Blackjack!")

    blackjack = Blackjack()
    blackjack.run()


if __name__ == '__main__':
    try:
        main()
    except UserWarning as e:
        print(f"Exception occurred: {e}")
    except Exception as e:
        print(f"Exception occurred: {e}")
        # TODO: Finish this
