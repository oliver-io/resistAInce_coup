import os
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI

from src.models.traits import AICharacterTraits

openai_api_key = os.getenv("OPENAI_API_KEY")


# a function which returns a RunnableSerializable given a name parameter:
def create_game_state_analyzer(name: str) -> RunnableSerializable:
    analyzer_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f""""You ({name}) are an AI-powered player in the game `The Resistance: Coup`.
You will be given MARKDOWN with two tables that contains the current state of the entire game, as is known to you.

I will give you `gamestate` which contains:
- The first table will contain a list of PLAYERS, their COINS, their visible CARDS.
- The second table will contain the current DECK count, the TREASURY coins remaining, and the DISCARD pile contents.
I will also give you `PAST_DIALOGUE` which contains a list of the dialogue that just occurred.
Please refer to all other players by NAME.  Your name is "{name}"

I would like for you to respond with a detailed analysis of the board.  This should contain, at least:
 - A breakdown of the current situation at large
 - A prediction for what each players' cards are (or UNKNOWN)
 - An analysis of what each player is postured to do and how likely they are to bluff given their conditions
 - An analysis of who is the greatest threat (to yourself) on the board, and what could be done to stop them
 - An analysis of who is a viable cooperator on the board, and how we might temporarily align with one another
 - Top immediate goal for your next turn, such as "get 1 more coin so that we can assassinate" or "get a Contessa card"
 
Please remember these hints:
    - "Income" is 1 coin, which is easy to confuse with "Tax", which is 3 coins and implies you hold a Duke
""",
            ),
            ("user", "{input}"),
        ]
    )

    return (
            analyzer_prompt | ChatOpenAI(openai_api_key=f"{openai_api_key}") | StrOutputParser()
    )



def analyzer_template(traits: AICharacterTraits, game_state_summary: str, last_round_dialogue: str) -> str:
    # at least for now game_state_summary comes padded in its own ticks
    return f"""
{game_state_summary}

```PAST_DIALOGUE
{last_round_dialogue}
```

"""