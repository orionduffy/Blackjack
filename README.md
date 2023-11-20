<!-- README copied from https://gist.github.com/DomPizzie/7a5ff55ffa9081f2de27c315f5018afc#file-readme-template-md -->
# Blackjack

A (currently CLI) Blackjack program with optional multiplayer

## Description

Allows a person to play Blackjack alone or host a server to play with friends. Some optional rules are not included or are simplified, but the goal was to create a fairly authentic Blackjack experience that is simple enough to be enjoyed by even people who are not used to the game.

## Getting Started

### Dependencies

* May not work with Python below 3.10 or above 3.11 (It has not been thoroughly tested on different versions)
* Requires the questionary package to be installed
* Requires either a normal terminal or an accurately emulated terminal due to questionary

### Installing

* Just download wherever you want, but keep all files in the same folder if possible.

### Executing program

* For singleplayer, just run main.py and choose "Singleplayer"
```
python main.py
```
\
\
* For multiplayer, someone must host the server
* If cheating is a concern, someone who is not playing could be chosen to host the server
```
python server.py
```
* The players must run main.py like they would for playing singleplayer but choose "Multiplayer"
* Players must choose a name, but a number based on when they joined the server will be added to the end, so there is no need to worry about overlap.
* The players must enter the IP of the server. Currently, the server lists the IP it bound to that players can use to connect to it.
* The game will then start.

## Help

* Running the program causes an error claiming something along the lines of the user not running it in a terminal:
This may happen in some IDEs if they do a simplified imitation of a terminal, since questionary needs advanced features. Most IDEs that do this have an option to more accurately emulate a terminal, or the program can just be run in a normal terminal.

## Authors

Orion Duffy

Nahom Demoz

## Version History

* 0.1
    * Initial Release

## License

This project is not currently licensed, but the creators reserve the right to change the license at a later data

## Acknowledgments
Jamal Bouajjaj - Professor of class this program was created for.