


class Player:

    def __init__(self, pname, connection):
        self.name = pname
        
        self.player_money = 100
    
        self.player_cards = []
        
        self.conn = connection
        self.status = "Hit (Draw another card)" 

    def initialize_new_game(self):
        self.player_cards = []
        self.status = "Hit (Draw another card)" 