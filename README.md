# Credit / Origins
The entire game engine in this piece of code is taken from https://github.com/dirkbrnd/resistance_coup

Credit where credit is due: to some wonderful dude in the gitlogs named **Dirk Brand** (-- and what a name).

# What is this?
Basically, I'm using LangChain as the brain of each player in the game and running it autonomously.  This means
that the original human flow is mostly deprecated, and you get to watch the players go-at-it in cyberspace.

# How work?
Currently, the flow is pretty simple, made up from a few different chains of OpenAI conversations:

![diagram](./assets/diagram.png)

- Each player takes in the state of the board and forms an "analysis" which is a summary of the current game-state.  They might be fed past dialogue as part of this state.
- Each "analysis" forms private intentions within the AI's model, which does not necessarily have to map to its decided action (for subterfuge and such).
- Each "private intention" is fed into a model which decides on a public action, and public statements, which might be lies.
- This speech is communicated to the other players, and then the process begins again!  In theory, the public statements of the AI will affect others' internal and public modes.

# Does it work?
Decide for yourself!  Keep reading for instructions on how to watch the wheelings-and-dealings of these virtual folks.

# How to Run
- All instructions henceforth are for Linux.  
- If you're on a 'mac, you're probably lucky and can pretend I didn't say Linux.
- If you're on Windows, bless your heart.

> Installation of correct Python Version and Check Out Code Stuff
```bash
# optional for currentness:
sudo apt update
sudo apt upgrade

# Required if ya aren't already running >= 3.11
sudo apt install python3.11-venv

# This not-so-optional and sets up:
git clone https://github.com/oliver-io/resistAInce_coup game && cd "$_"
python3.11 -m venv env
source env/bin/activate
```

> Install Dependencies
```bash
poetry install
```

> Run the Game
```bash
python coup.py
```

:rocket: