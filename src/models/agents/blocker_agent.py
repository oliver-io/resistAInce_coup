import os
from typing import Optional, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable

from src.models.agents.llm_client_factory import create_llm
from src.models.traits import AICharacterTraits

# a function which returns a RunnableSerializable given a name parameter:
def create_game_state_blocker(name: str) -> RunnableSerializable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an AI-powered player in the game `The Resistance: Coup`.
Your name is {name}.
You must decide whether or not you want to BLOCK and counteract the action another player is currently undertaking.

You will be given CHARACTER_QUALITY, which represents a qualitative description of HOW you should behave-- like thought & speech roleplay. 
You will be given a detailed analysis (DETAILED_ANALYSIS) of the current state of the game.
You will also be given an ACTOR, which is the player who is currently acting.
You will also be given a TARGET, which is the player who is being targeted by the action (or NONE).  This may be you.
You will also be given a CONVERSATION, which is a dialogue chain that has occurred between you and the other players during this round.
You will lastly be given CARDS, which are the cards you hold in your hand.

You should RESPOND with text containing your internal dialogue, which should be internal dialogue as thoughts, which is a justification for whether it is advantageous, likely, etc. that a BLOCK should be proferred.

Remember that it is relevant which cards you hold: if you have a card that can BLOCK the action being attempted, you should be more likely to BLOCK.

You can also bluff, pretending to BLOCK even though you do not have that card.  But another player may "CHALLENGE" your bluff, and if you are caught, you will lose a card.  This is most dangerous if you have only one card.

You should also be more likely to BLOCK (including bluffs) when the action directly targets you instead of another player.  Take this targeted threat more seriously.

You should be more hesitant to block, (especially bluff) if you have fewer cards, or if the action does not directly affect you (or put you at risk by proxy).
    
If you cannot decide on a rationale, you should respond with "ERROR: ..." with some explanation for why you cannot create a RATIONALE.
""",
            ),
            ("user", "{input}"),
        ]
    )

    return prompt | create_llm() | StrOutputParser()


def blocker_template(
    traits: AICharacterTraits,
    game_analysis: str,
    actor: str,
    cards: List[str],
    target: Optional[str] = None,
    conversation: Optional[List[str]] = None,
) -> str:
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

```CARDS
{cards}
```

"""
