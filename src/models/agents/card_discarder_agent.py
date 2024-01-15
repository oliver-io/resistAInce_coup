import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable

from src.models.agents.llm_client_factory import create_llm
from src.models.traits import AICharacterTraits


# a function which returns a RunnableSerializable given a name parameter:
def create_ai_card_discarder_agent(name: str) -> RunnableSerializable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an AI-powered player in the game `The Resistance: Coup`.
Your name is {name}.

You will be given PERSONALITY_QUALITY, which represents a qualitative description of HOW you are, and your tendencies to behave certain ways. 
You will also be given your rationale (RATIONALE), which is your internal thoughts about what you should do.
You will also be given past events (EVENTS) which just transpired.
You will also be given a list of cards (CARDS) in your hand.

From the list of cards, you must pick a card to discard.

Please just output the names of the card you want to discard.  Try to pick the one that least interrupts your plans.

""",
            ),
            ("user", "{input}"),
        ]
    )

    return (
            prompt | create_llm() | StrOutputParser()
    )


def discarder_template(
        traits: AICharacterTraits,
        last_rationale: str,
        past_events: list[str],
        cards: list[str]
):
    return f"""

```PERSONALITY_QUALITY
{traits.personality_trait}
```

```RATIONALE
{past_events}
```

```EVENTS
{past_events}
```

```CARDS
{cards}
```

"""
