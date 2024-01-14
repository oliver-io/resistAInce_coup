import os
from typing import Optional, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI

from src.models.traits import AICharacterTraits

openai_api_key = os.getenv("OPENAI_API_KEY")

# a function which returns a RunnableSerializable given a name parameter:
def create_game_state_challenger(name: str) -> RunnableSerializable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an AI-powered player in the game `The Resistance: Coup`.
Your name is {name}.
You must decide whether or not you want to CHALLENGE the action another player is currently undertaking.

You will be given CHARACTER_QUALITY, which represents a qualitative description of HOW you should behave-- like thought & speech roleplay. 
You will be given a detailed analysis (DETAILED_ANALYSIS) of the current state of the game.
You will also be given an ACTOR, which is the player who is currently acting.
You will also be given a TARGET, which is the player who is being targeted by the action (or NONE).  This may be you.
You will also be given a CONVERSATION, which is a dialogue chain that has occurred between you and the other players during this round.

You should RESPOND with text containing your internal dialogue, which should be internal dialogue as thoughts, which is a justification for whether it is advantageous, likely, etc. that a challenge should be proferred.
    
If you cannot decide on a rationale, you should respond with "ERROR: ..." with some explanation for why you cannot create a RATIONALE.

You should be more hesitant to challenge if you have fewer cards, or if the action does not directly affect you (or put you at risk by proxy).

If the action does target you, you should take the threat more seriously.
""",
            ),
            ("user", "{input}"),
        ]
    )

    return (
            prompt | ChatOpenAI(openai_api_key=f"{openai_api_key}") | StrOutputParser()
    )

def challenger_template(traits: AICharacterTraits, game_analysis: str, actor: str, target: Optional[str] = None, conversation: Optional[List[str]] = None) -> str:
    return f"""
```CHARACTER_QUALITY
- Personality: You {traits.personality_trait}
- Speech: You {traits.speech_trait}
```

```DETAILED_ANALYSIS
{game_analysis}
```

```ACTOR
{actor}
```

```TARGET
{target}
```

```CONVERSATION
{conversation}
```
"""

