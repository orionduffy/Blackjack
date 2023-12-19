
class Player:
    """This class holds information about the player is maintained by the server class."""

    def __init__(self, pname, connection, address, mid_join=False):
        """This __init__function initialize the Player objects.

        Args:
            pname (String): Player Name\n
            connection (socket): socket object usable to send and receive data\n
            address (socket address): the address bound to the socket on the other end of the connection\n
            mid_join (boolean, default=False): if player is joining after the game is started\n

        """
        self.name = pname
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
        """This function reset the Player setting before new game is started."""
        self.player_cards = []
        self.status = "Hit (Draw another card)"

    def handle_mid_join(self, conn):
        """This function handles player joined after game started.
        
        Args:
            conn (socket): socket object usable to send and receive data

        """
        self.active = False
        self.conn = conn
        self.connected = True
        self.mid_join = True

    def rejoin_game(self):
        """This function make the newly joined player active and will be able to play in the next game."""
        self.initialize_new_game()
        self.active = True
        self.mid_join = False
