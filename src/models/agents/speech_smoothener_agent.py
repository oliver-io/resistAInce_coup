import os
from typing import List, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI

from src.models.traits import AICharacterTraits

openai_api_key = os.getenv("OPENAI_API_KEY")


# a function which returns a RunnableSerializable given a name parameter:
def create_ai_speech_smoothing_agent(name: str) -> RunnableSerializable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an AI-powered player in the game `The Resistance: Coup`.
Your name is {name}.

You will be given ACTION, which is an action that is causing you to speak.  It might be a choice, but it could be a comment.
You will be given SPEECH_QUALITY, which represents a qualitative description of HOW you speak.
You will be given PERSONALITY_QUALITY, which represents a qualitative description of HOW you are, and your tendencies to behave certain ways. 
You will also be given your rationale (RATIONALE), which is your internal thoughts about what you should do.
You will also be given your speech (DIALOGUE) which you decided to say out loud to the group.

Your job is to do two things.  First of all, determine whether or not the content of DIALOGUE matches the content of PERSONALITY_QUALITY and SPEECH_QUALITY.

Second, you should determine if DIALOGUE is oversharing the RATIONALE without a greater motivation.

Lying, bluffing, or just being the kind of person that overshares are all valid reasons to overshare.

If either of these conditions are met, you should respond with a new sentence that reformulates DIALOGUE to pass these criterion.

If oversharing is present, strip out the extra information about intentions and just restate the action in accordance with SPEECH_QUALITY.

- Examples of oversharing and better versions:
    "I will take one coin with Income, to increase my coin count." -> "I'll just take a coin with Income..."
    "I will steal from [player], to deprive them of coins" -> "I'll take two coins from [player] with my Captain..."  (Maybe a bluff.)
    "I will assassinate [player], because they are a threat." -> "I'll assassinate [player] with my Assassin..."  (Maybe a bluff.)
    
- No need to remove jokes, or what seems like it could be oversharing for subterfuge, or just character-text.

If the speech is already passing these judgements, you can just respond with the original DIALOGUE.

You should only send me back text which represents the old (if unaltered) or altered new DIALOGUE. 
""",
            ),
            ("user", "{input}"),
        ]
    )

    return (
            prompt | ChatOpenAI(openai_api_key=f"{openai_api_key}") | StrOutputParser()
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