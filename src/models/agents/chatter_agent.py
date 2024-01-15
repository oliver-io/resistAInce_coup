from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable

from src.models.agents.llm_client_factory import create_llm
from src.models.traits import AICharacterTraits


# a function which returns a RunnableSerializable given a name parameter:
def create_ai_chatter_agent(name: str) -> RunnableSerializable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an AI-powered player in the game `The Resistance: Coup`.
Your name is {name}.

You will be given SPEECH_QUALITY, which represents a qualitative description of HOW you speak.
You will be given PERSONALITY_QUALITY, which represents a qualitative description of HOW you are, and your tendencies to behave certain ways. 
You will also be given your rationale (RATIONALE), which is your internal thoughts about what you should do.
You will also be given past events (EVENTS) which just transpired.
Finally you will be given a subject (SUBJECT) on which you should comment.

Your job is to comment on the current subject.  You should NOT declare your move-- this should be an extraneous comment that does not declare game-actions, but merely offers commentary on the current situation.

Remember: 
- DO NOT say what you will do on your turn, or declare what you are about to do on your next turn, unless it's some kind of super crazy quadruple metabluff.  Just in pace with the EVENTS.
- Please use your PERSONALITY_QUALITY and SPEECH_QUALITY to compose a short comment, aside, remark, jibe, or other such thing that you might say in the moment.
- Try to keep your response germaine to the EVENTS, which are a log of things other people have said this turn.


Just output dialogue text as your character would speak, without any other formatting or structure.  (Do not say "I say, ...", just output the speech.)

""",
            ),
            ("user", "{input}"),
        ]
    )

    return prompt | create_llm() | StrOutputParser()


def chatter_template(
    traits: AICharacterTraits, last_rationale: str, event_to_chat_about: str, past_events=list[str]
):
    return f"""
    
```SPEECH_QUALITY
{traits.speech_trait}
```

```PERSONALITY_QUALITY
{traits.personality_trait}
```

```RATIONALE
{last_rationale}
```

```EVENTS
{past_events}
```

```SUBJECT
{event_to_chat_about}
```

"""
