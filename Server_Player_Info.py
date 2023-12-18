
class Player:

    def __init__(self, pname, pindex, connection, address, mid_join=False):
        self.name = pname + str(pindex)
        self.pname = pname
        # The socket stores the address and port in the same tuple.
        # By doing address[0], other parts only have to send the tuple without worrying about specifically sending
        self.address = address[0]
        self.active = True

        self.player_money = 100
        self.player_cards = []
        self.status = "Hit (Draw another card)"
        
        self.conn = connection
        self.connected = True

        self.mid_join = mid_join
        if self.mid_join:
            self.handle_mid_join(connection)

    def initialize_new_game(self):
        self.player_cards = []
        self.status = "Hit (Draw another card)"

    def handle_mid_join(self, conn):
        self.active = False
        self.conn = conn
        self.connected = True
        self.mid_join = True

    def rejoin_game(self):
        self.initialize_new_game()
        self.active = True
        self.mid_join = False
