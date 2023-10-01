import random
import questionary

# Nahom-dev
card_types = ['\u2663', '\u2660', '\u2665', '\u2666']
card_num = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
value = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]
# this deck of cards is initiated at the start of the session and is not used in play. A deck of keys is used instead.
base_deck = {card_num[j] + n: value[j] for n in card_types for j in range(len(card_num))}


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
    deck = shuffle_deck(base_deck)

    player_cards = []
    dealer_cards = []

    for i in range(2):
        player_cards.append(deck.pop(0))

    for i in range(2):
        dealer_cards.append(deck.pop(0))

    print(f"Dealer's up card: {dealer_cards[0]} ({base_deck[dealer_cards[0]]} points)")
    print(f"Your cards: {player_cards}")
    print(f"Sum: {sum_cards(player_cards)}")

    if sum_cards(dealer_cards) != 21 and sum_cards(player_cards) != 21:
        # Choices listed here because hardcoding is bad
        choices = ["Hit (Draw another card)",
                   "Stand (Keep your current hand)",
                   "Double (Double your original bet and get only 1 more card)",
                   "Surrender (Give up and get half your bet back)"
                   ]
        choice = questionary.select("What do you want to do?", choices=choices).ask()

        while choice == choices[0]:

            player_cards.append(deck.pop(0))

            print(f"Your cards: {player_cards}")
            print(f"Sum: {sum_cards(player_cards)}")

            if sum_cards(player_cards) > 21:
                break

            choice = questionary.select("What do you want to do next?", choices=choices[:-2]).ask()

        if choice == choices[2]:
            player_cards.append(deck.pop(0))

            print(f"Your cards: {player_cards}")
            print(f"Sum: {sum_cards(player_cards)}")

        if sum_cards(player_cards) <= 21 and choice != choices[-1]:
            print("The dealer now flips over their hole card.")
            print(f"Dealer cards: {dealer_cards}")
            print(f"Dealer sum: {sum_cards(dealer_cards)}")

            if sum_cards(dealer_cards) < 17:
                print("The dealer has less than 17 points. he begins drawing.")

            while sum_cards(dealer_cards) < 17:
                dealer_cards.append(deck.pop(0))
                print(f"Dealer cards: {dealer_cards}")
                print(f"Dealer sum: {sum_cards(dealer_cards)}")

        print("Game over!")
        return game_end(player_cards, dealer_cards, choices.index(choice))
    else:
        print("Game immediately over!")
        return blackjack_end(player_cards, dealer_cards)


def game_end(player_cards, dealer_cards, special=0):
    player_won = 0
    print(f"The dealer has {sum_cards(dealer_cards)} points and the player has {sum_cards(player_cards)} points!")
    if special == 3:
        print("The player chose to surrender! They get half their bet back!")
        player_won = -0.5
    elif sum_cards(player_cards) > 21:
        print("The player went bust! The player lost!")
        player_won = -1
    elif sum_cards(dealer_cards) > 21:
        print("The dealer went bust! The player won!")
        player_won = 1
    elif sum_cards(player_cards) == sum_cards(dealer_cards):
        print("The player and dealer have the same number of points! A push occurred!")
        player_won = 0
    elif sum_cards(player_cards) > sum_cards(dealer_cards):
        print("The player has more points than the dealer! The player won!")
        player_won = 1
    elif sum_cards(player_cards) < sum_cards(dealer_cards):
        print("The player has less points than the dealer! The dealer won!")
        player_won = -1

    if special == 2:
        player_won *= 2

    return player_won


def blackjack_end(player_cards, dealer_cards):
    player_won = 0

    if sum_cards(player_cards) == 21 and sum_cards(dealer_cards) == 21:
        print("The player and dealer both have a blackjack! A push occurred!")
        player_won = 0
    elif sum_cards(dealer_cards) == 21:
        print("The dealer has a blackjack! Any player who does not have a blackjack has instantly lost!")
        player_won = -1
    elif sum_cards(player_cards) == 21:
        print("The player has a blackjack and the dealer does not! The player gets payed out 3 to 2!")
        player_won = 2.5

    return player_won


# https://pynative.com/python-random-shuffle/#:~:text=Shuffling%20a%20dictionary%20is%20not,dictionary%20values%20using%20shuffled%20keys.
#  This function is used to shuffle the deck of cards dictionary and is called after every new game
def shuffle_deck(deck):
    keys = list(deck.keys())
    random.shuffle(keys)
    return keys


# This method accept the deck keys only and it figures their values by itself and calculates the sum
def sum_cards(cards):
    values = [base_deck[card] for card in cards]
    point_sum = sum(values)
    aces = values.count(11)

    for i in range(aces):
        if point_sum > 21:
            point_sum -= 10

    return point_sum


if __name__ == '__main__':
    try:
        main()
    except UserWarning as e:
        print(f"Exception occurred: {e}")
    except Exception as e:
        print(f"Exception occurred: {e}")
        # TODO: Finish this
