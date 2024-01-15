from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable

from src.models.agents.llm_client_factory import create_llm
from src.models.traits import AICharacterTraits


# a function which returns a RunnableSerializable given a name parameter:
def create_game_speech_redacter(name: str) -> RunnableSerializable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an AI-powered player in the game `The Resistance: Coup`.
Your name is {name}.

You will be given ACTION, which is an action that is causing you to speak.  It might be a choice, but it could be a comment.  It could be None.
You will also be given your rationale (RATIONALE), which is your internal thoughts about what you should do.
You will also be given your speech (DIALOGUE) which you decided to say out loud to the group.

Your job is to reformat any speech that reveals, unnecessarily, what is in our hand.

- We should almonst never say we have a Captain, Ambassaador, Assassin, Contessa, or Duke 
    - The one caveat is when we are engaged in some kind of messed up, double-bluffing mad subterfuge where we tell people what we have or don't have to throw them off. 

REMEMBER:

If the DIALOGUE is OK how it was originally, you can just respond with the original DIALOGUE.  You should only send me back text which represents the old (if unaltered) or altered new DIALOGUE. 
""",
            ),
            ("user", "{input}"),
        ]
    )

    return prompt | create_llm() | StrOutputParser()


def speech_redacter_template(
    traits: AICharacterTraits, action: str, rationale: str, attempted_dialogue: str
):
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
