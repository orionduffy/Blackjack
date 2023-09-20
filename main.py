import random


# Runs a game of Blackjack
def main():
    print("Welcome to Blackjack!")

    player_money = 100
    choice = ""

    while player_money > 0 and choice != "q":
        bet = 0
        while bet == 0:
            try:
                bet_input = input(f"You have ${player_money}. Please choose how much you'd like to bet: ")
                bet = int(bet_input)
                if bet > player_money:
                    print("Error! Bet is too much! You don't have that much money!")
                    bet = 0
            except ValueError:
                print("Error! Invalid input! Must be a number!")

        player_money -= bet
        print(f"${bet} will be bet! You have ${player_money} left in reserve! Beginning game!")

        multiplier = play_blackjack()

        player_money += bet * multiplier
        player_money = int(player_money)

        choice = ""
        while (choice != "q" and choice != "c") and player_money > 0:
            choice = input("Would you like to quit now (q), or continue (c)? ")
            if choice != "q" and choice != "c":
                print(f"Error! Response must be \"q\" or \"c\"! You typed: {choice}")

    print(f"Thank you for playing. You left with ${player_money}")



# Runs the core game loop
def play_blackjack():
    deck = []
    for i in range(4):
        deck += [i for i in range(1, 12)]
    for i in range(8):
        deck.append(10)

    random.shuffle(deck)

    player_cards = []
    dealer_cards = []

    choice = ""

    while choice != "k":

        for i in range(2):
            player_cards.append(deck.pop(0))

        if sum(dealer_cards) < 17:
            for i in range(2):
                dealer_cards.append(deck.pop(0))

        bust(player_cards)

        print(f"Your cards: {player_cards}")
        print(f"Sum: {sum(player_cards)}")

        if bust(player_cards) or bust(dealer_cards):
            break

        choice = ""
        while choice != "k" and choice != "d":
            choice = input("Would you like to keep your cards (k), or draw again (d)? ")
            if choice != "k" and choice != "d":
                print(f"Error! Response must be \"k\" or \"d\"! You typed: {choice}")

    print("Game over!")
    return game_end(player_cards, dealer_cards)


def game_end(player_cards, dealer_cards):
    player_won = 1
    print(f"The dealer has {sum(dealer_cards)} points and the player has {sum(player_cards)} points!")
    if bust(player_cards):
        print("The player went bust! The player lost!")
        player_won = 0
    elif bust(dealer_cards):
        print("The dealer went bust! The player won!")
        player_won = 2
    elif sum(player_cards) == sum(dealer_cards):
        print("The player and dealer have the same number of points! A push occurred!")
        player_won = 1
    elif sum(player_cards) > sum(dealer_cards):
        print("The player has more points than the dealer! The player won!")
        player_won = 2
    elif sum(player_cards) < sum(dealer_cards):
        print("The player has less points than the dealer! The dealer won!")
        player_won = 0

    if player_won == 2 and sum(player_cards) == 21:
        print("Additionally, the player got blackjack! Earnings increased!")
        player_won = 2.5

    return player_won

# Returns TRUE if user went bust
def bust(cards):
    if sum(cards) > 21:
        while 11 in cards:
            cards[cards.index(11)] = 1
            if sum(cards) <= 21:
                break
        if sum(cards) <= 21:
            return False
        else:
            return True
    else:
        return False


if __name__ == '__main__':
    try:
        main()
    except UserWarning as e:
        print(f"Exception occurred: {e}")
    except Exception as e:
        print(f"Exception occurred: {e}")
        # TODO: Finish this
