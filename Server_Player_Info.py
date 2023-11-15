
class Player:

    def __init__(self, pname, connection):
        self.name = pname
        self.active = True

        self.player_money = 100
        self.player_cards = []
        self.status = "Hit (Draw another card)"
        
        self.conn = connection
        self.connected = True

    def initialize_new_game(self):
        self.player_cards = []
        self.status = "Hit (Draw another card)"
