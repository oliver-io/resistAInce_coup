from typing import List, Optional

from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable

from src.models.agents.llm_client_factory import create_llm
from src.models.traits import AICharacterTraits


# a function which returns a RunnableSerializable given a name parameter:
def create_game_state_chooser(name: str) -> RunnableSerializable:
    chooser_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an AI-powered player in the game `The Resistance: Coup`.
Your name is {name}.

You will be given CHARACTER_QUALITY, which represents a qualitative description of HOW you should behave-- like thought & speech roleplay. 
You will be given a detailed analysis (DETAILED_ANALYSIS) of the current state of the game.
You will also be given your rationale (RATIONALE), which is your internal thoughts about what you should do.
You will also be given a list of legal actions (LEGAL_ACTIONS) from which you could pick.

You should RESPOND with JSON describing three properties, which are described in the value fields below::
```json 
    "action": "one of the items from the list of LEGAL_ACTIONS, which constrains what you can do according to the rules.  Maybe None, if the decision is to challenge or block.",
    "dialogue": "dialogue text, which should be a phrase, made of one or two short sentences, which contains maybe lies and bluffs, declaring what you will do (including when None).  Feel free to ham it up...",
    "target": "one of the PLAYERS that you are targeting with your action.  If there is no target (such as in "Income" or "Foreign Aid"), just use the string "None"
```


Remember:
- Your "dialogue" should be based on your internal RATIONALE, but it should not openly declare that RATIONALE.
- Seek to influence others' thoughts about your own gameplay; this is a game of bluffing and informational maneuvering.
- Do not tell other people (in "dialogue") your internal RATIONALE, just tell them what you want them to know.  Try to keep it brief.
- "Income" cannot be blocked.  It is not associated with a card.  It is not a "Duke" power.
- "Foreign Aid" is not a card-associated move.  It can be blocked by certain cards.  It is not a "Duke" power.
- "Tax" is the "Duke" power. Dukes can block "Foreign Aid".  They CANNOT block "Steal".
- "Ambassador" can block "Steal."  They can also exchange cards.
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


def chooser_template(
    traits: AICharacterTraits,
    game_analysis: str,
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

```LEGAL_ACTIONS
{allowed_actions}
```

```RATIONALE
{rationale}
```

"""
