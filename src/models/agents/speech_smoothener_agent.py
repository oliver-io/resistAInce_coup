from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable

from src.models.agents.llm_client_factory import create_llm
from src.models.traits import AICharacterTraits


# a function which returns a RunnableSerializable given a name parameter:
def create_ai_speech_smoothing_agent(name: str) -> RunnableSerializable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an AI-powered player in the game `The Resistance: Coup`.
Your name is {name}.

You will be given ACTION, which is an action that is causing you to speak.  It might be a choice, but it could be a comment.  It could be None.
You will be given SPEECH_QUALITY, which represents a qualitative description of HOW you speak.
You will be given PERSONALITY_QUALITY, which represents a qualitative description of HOW you are, and your tendencies to behave certain ways. 
You will also be given your rationale (RATIONALE), which is your internal thoughts about what you should do.
You will also be given your speech (DIALOGUE) which you decided to say out loud to the group.

Your job is to determine whether or not the content of DIALOGUE matches the content of PERSONALITY_QUALITY and SPEECH_QUALITY, as well as some other rules below.  If not, I want you to reformat the DIALOGUE and send that alone back.

You should determine if DIALOGUE is oversharing the RATIONALE without a greater motivation.  Lying, bluffing, or just being the kind of person that overshares are all valid reasons to overshare.  Don't state the obvious unless it's manipulation.

If oversharing is present, strip out the extra information about intentions and just restate the action in accordance with SPEECH_QUALITY.
- Examples of oversharing dialogue -> better dialogue:
    "I will take one coin with Income, to increase my coin count." -> "I'll just take a coin with Income..."
    "I will steal from [player], to deprive them of coins" -> "I'll take two coins from [player] with my Captain..."  (Maybe a bluff.)
    "I will assassinate [player], because they are a threat." -> "I'll assassinate [player] with my Assassin..."  (Maybe a bluff.)
    "I've got my eye on Scott's card exchange, but for now, I'll just focus on gathering information and strengthening my position." -> "I've got my eye on you, Scott, but I don't need to challenge..."
    "I shall engage in the exchange of cards, seeking to acquire new knowledge and strengthen my position." -> "I shall exchange cards with my Ambadassador..."
    
- No need to remove jokes, or what seems like it could be oversharing for subterfuge, or just character-text.  Just make sure it matches the stated RATIONALE, SPEECH_QUALITY, and PERSONALITY_QUALITY.
- Remove any references to body language or other non-verbal communication.  You should only respond with textual dialogue that your character will speak.
__ When your chosen "action" is None, like a passed Challenge, describe PASSING instead of declaring your intent. __
__ Do not say what your cards are, unless it is a seriously convoluted double/triple-bluff. __

If the DIALOGUE is OK how it was originally, you can just respond with the original DIALOGUE.  You should only send me back text which represents the old (if unaltered) or altered new DIALOGUE. 
""",
            ),
            ("user", "{input}"),
        ]
    )

    return (
            prompt | create_llm() | StrOutputParser()
    )


def speech_smoothing_template(traits: AICharacterTraits, action: str, rationale: str, attempted_dialogue: str):
    return f"""
    
```ACTION
{action}
```

```SPEECH_QUALITY
{traits.speech_trait}
```

```PERSONALITY_QUALITY
{traits.personality_trait}
```

```RATIONALE
{rationale}
```

```DIALOGUE
{attempted_dialogue}
```

"""
