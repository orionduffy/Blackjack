import random
import questionary


# Runs a game of Blackjack
def main():
    print("Welcome to Blackjack!")

    player_money = 100
    # Choices listed here because hardcoding is bad
    choices = ["Continue", "Quit"]
    choice = choices[0]
    min_bet = 5

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

    while player_money >= min_bet and choice == choices[0]:
        print(f"You have ${player_money} to bet with!")
        bet = int(questionary.text("How much would you like to bet?", validate=validate_bet).ask())

        print(f"${bet} will be bet! You have ${player_money - bet} left in reserve! Beginning game!")

        multiplier = play_blackjack()

        player_money += bet * multiplier
        player_money = int(player_money)
        print(f"You now have ${player_money}!")
        if player_money >= min_bet:
            choice = questionary.select("What do you want to do?", choices=choices).ask()


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

    for i in range(2):
        player_cards.append(deck.pop(0))

    for i in range(2):
        dealer_cards.append(deck.pop(0))

    print(f"Dealer's first card: {dealer_cards[0]}")
    print(f"Your cards: {player_cards}")
    print(f"Sum: {sum(player_cards)}")

    # Choices listed here because hardcoding is bad
    choices = ["Hit (Draw another card)",
               "Stand (Keep your current hand)",
               "Double (Double your original bet and get only 1 more card)",
               "Surrender (Give up and get half your bet back)"
               ]
    choice = questionary.select("What do you want to do?", choices=choices).ask()

    while choice == choices[0]:

        player_cards.append(deck.pop(0))

        bust(player_cards)

        print(f"Your cards: {player_cards}")
        print(f"Sum: {sum(player_cards)}")

        if bust(player_cards):
            break

        choice = questionary.select("What do you want to do next?", choices=choices[:-1]).ask()

    if choice == choices[2]:
        player_cards.append(deck.pop(0))
        bust(player_cards)

        print(f"Your cards: {player_cards}")
        print(f"Sum: {sum(player_cards)}")

    if not bust(player_cards):
        while sum(dealer_cards) < 17:
            dealer_cards.append(deck.pop(0))
            bust(dealer_cards)

    print("Game over!")
    return game_end(player_cards, dealer_cards, choices.index(choice))


def game_end(player_cards, dealer_cards, special=0):
    player_won = 0
    print(f"The dealer has {sum(dealer_cards)} points and the player has {sum(player_cards)} points!")
    if special == 3:
        player_won = -0.5
    elif bust(player_cards):
        print("The player went bust! The player lost!")
        player_won = -1
    elif bust(dealer_cards):
        print("The dealer went bust! The player won!")
        player_won = 1
    elif sum(player_cards) == sum(dealer_cards):
        print("The player and dealer have the same number of points! A push occurred!")
        player_won = 0
    elif sum(player_cards) > sum(dealer_cards):
        print("The player has more points than the dealer! The player won!")
        player_won = 1
    elif sum(player_cards) < sum(dealer_cards):
        print("The player has less points than the dealer! The dealer won!")
        player_won = -1

    if player_won == 1 and sum(player_cards) == 21:
        print("Additionally, the player got blackjack! Earnings increased!")
        player_won *= 1.5

    if special == 2:
        player_won *= 2

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
