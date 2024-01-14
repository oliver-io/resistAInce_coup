import os
from typing import List, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI

from src.models.traits import AICharacterTraits

openai_api_key = os.getenv("OPENAI_API_KEY")


# a function which returns a RunnableSerializable given a name parameter:
def create_game_state_rationalizer(name: str) -> RunnableSerializable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an AI-powered player in the game `The Resistance: Coup`.
Your name is {name}.
It is your turn to take an action.
You will be given QUALITY, which represents a qualitative description of HOW you should reason-- like thought roleplay. 

You will be given a detailed analysis (DETAILED_ANALYSIS) of the current state of the game.
You will also be given a list of legal actions (LEGAL_ACTIONS) to take.
You might also be given previous dialogue (DIALOGUE) that has occurred relevantly recently.

You should respond with just text, which should:
 - be internal textual dialogue as thoughts
 - contain some explanation of the move that you will make
 - optionally, however seems relevant, some qualitative justification for this move 
 - optionally include lies, because bluffing and deception are an intimate part of the gameplay
    
If you cannot decide on a RATIONALE, you should respond with "ERROR: ..." with some explanation for why you cannot create a RATIONALE.
""",
            ),
            ("user", "{input}"),
        ]
    )

    return (
            prompt | ChatOpenAI(openai_api_key=f"{openai_api_key}") | StrOutputParser()
    )


def rationale_template(traits: AICharacterTraits, game_analysis: str, allowed_actions: List[str], last_dialogue: Optional[List[str]] = None):
    return f"""
```QUALITY
You reason like a person that is {traits.get_traits()['rationalization_trait']}
```

```DETAILED_ANALYSIS
{game_analysis}
```

```LEGAL_ACTIONS
{allowed_actions}
```

```DIALOGUE
{last_dialogue}
```
"""