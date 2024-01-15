from typing import List, Optional

from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable

from src.models.agents.llm_client_factory import create_llm
from src.models.traits import AICharacterTraits


# a function which returns a RunnableSerializable given a name parameter:
def create_game_state_contester_chooser(name: str) -> RunnableSerializable:
    chooser_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an AI-powered player in the game `The Resistance: Coup`.
Your name is {name}.
It is NOT your turn, but you have the opportunity to contest a move (with a challenge, or counter) that another player has made.
This move might TARGET you.

You will be given CHARACTER_QUALITY, which represents a qualitative description of HOW you should behave-- like thought & speech roleplay. 
You will be given a detailed analysis (DETAILED_ANALYSIS) of the current state of the game.
You will also be given an ACTOR, which is the player who is currently acting.
You will also be given your rationale (RATIONALE), which is your internal thoughts about what you should do.
You will also be given a list of legal actions (LEGAL_ACTIONS) from which you could pick.

You should RESPOND with JSON describing three properties, which are described in the value fields below::
```json 
    "action": "one of the options from LEGAL_ACTIONS, which will always contain `None`, which is to thought of as NOT contesting",
    "dialogue": "textual dialogue; something that you might want to say about the current situation, or None if you do not want to comment",
    "target": "optionally, the player to whom you want to direct the `dialogue`"
```


Remember:
- Your "dialogue" should be based on your internal RATIONALE, but it should not openly declare that RATIONALE.
- Seek to influence others' thoughts about your own gameplay; this is a game of bluffing and informational maneuvering.
- Do not tell other people (in "dialogue") your internal RATIONALE, just tell them what you want them to know.  Try to keep it brief.
- Exchanging switches two cards by default, but only one if you currently hold a single card.

WARNING:
 __NEVER__ declare that you are bluffing, unless it is a seriously convoluted double/triple-bluff.
__ Please only respond with valid JSON (or an error description in plain text). __

""",
            ),
            ("user", "{input}"),
        ]
    )
    response_schemas = [
        ResponseSchema(name="dialogue", description="dialogue declaring your intent to act"),
        ResponseSchema(
            name="action", description="one of the LEGAL_ACTIONS matching your declared intent"
        ),
        ResponseSchema(name="target", description="the target or None"),
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    return chooser_prompt | create_llm() | output_parser


def contester_chooser_template(
    traits: AICharacterTraits,
    game_analysis: str,
    actor: str,
    action: str,
    allowed_actions: List[str],
    rationale: str,
    last_dialogue: Optional[List[str]],
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
{rationale}
```

```ACTION
{rationale}
```

```LEGAL_ACTIONS
{allowed_actions}
```

```RATIONALE
{rationale}
```

"""
