import os
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI
from pydantic.dataclasses import dataclass
from typing import Optional, List, Dict, Union, Tuple

from src.models.action import ActionType

openai_api_key = os.getenv('OPENAI_API_KEY')

class MyConfig:
    validate_assignment = False


@dataclass(config=MyConfig)
class AIGameAgent:
    analyzer: RunnableSerializable = None  # Set default to None
    rationalizer: RunnableSerializable = None  # Set default to None
    reacter: RunnableSerializable = None  # Set default to None
    dialoguer: RunnableSerializable = None  # Set default to None
    name: str = "None"

    def __init__(self, name: str):
        self.name = name

    def __post_init__(self):
        # Initialize ChatOpenAI here
        analyzer_prompt = ChatPromptTemplate.from_messages([
            ("system", f""""You ({self.name}) are an AI-powered player in the game `The Resistance: Coup`.
You will be given MARKDOWN with two tables that contains the current state of the entire game, as is known to you.

The first table will contain a list of PLAYERS, their COINS, their visible CARDS.
The second table will contain the current DECK count, the TREASURY coins remaining, and the DISCARD pile contents.
Please refer to all players by NAME.  Your name is "{self.name}"

I would like for you to respond with a detailed analysis of the board.  This should contain, at least:
 - A breakdown of the current situation at large
 - A prediction for what each players' cards are (or UNKNOWN)
 - An analysis of what each player is postured to do and how likely they are to bluff given their conditions
 - An analysis of who is the greatest threat (to yourself) on the board, and what could be done to stop them
 - An analysis of who is a viable cooperator on the board, and how we might temporarily align with one another
 - Top immediate goal for your next turn, such as "get 1 more coin so that we can assassinate" or "get a Contessa card"
"""),
            ("user", "{input}")
        ])

        self.analyzer = analyzer_prompt | ChatOpenAI(
            openai_api_key=f"{openai_api_key}"
        ) | StrOutputParser()

        rationalizer_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an AI-powered player in the game `The Resistance: Coup`.
Your name is {self.name}.
It is your turn to take an action.

You will be given a detailed analysis (DETAILED_ANALYSIS) of the current state of the game.
You will also be given a list of legal actions (LEGAL_ACTIONS) to take.

You should RESPOND with internal dialogue text, which should be internal textual dialogue as thoughts, which contains some explanation of the move that you will make, and optionally, however seems relevant, some justification for this move (including lies, because bluffing and deception are an intimate part of the gameplay here).
    
If you cannot decide on a RATIONALE, you should respond with "ERROR: ..." with some explanation for why you cannot create a RATIONALE.
"""
             ),
            ("user", "{input}")
        ])
        self.rationalizer = rationalizer_prompt | ChatOpenAI(
            openai_api_key=openai_api_key) | StrOutputParser()  # | ActionDialogueExtractor

        dialoguer_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an AI-powered player in the game `The Resistance: Coup`.
Your name is {self.name}.

You will be given a detailed analysis (DETAILED_ANALYSIS) of the current state of the game.
You will also be given your rationale (RATIONALE), which is your internal thoughts about what you should do.
You will also be given a list of legal actions (LEGAL_ACTIONS) from which you could pick.

You should RESPOND with JSON describing three properties, which are described in the value fields below::
```json
    "dialogue": "internal dialogue text, which should be a phrase, made of one or two short sentences, which contains maybe lies and bluffs, declaring what you will do.  Feel free to ham it up...",
    "action": "one of the items from the list of LEGAL_ACTIONS, which constrains what you can do according to the rules.",
    "target": "one of the PLAYERS that you are targeting with your action.  If there is no target (such as in "Income" or "Foreign Aid"), just send `None`"
```
    
Remember your dialogue should be based on your internal RATIONALE, but it should not openly declare that RATIONALE, but instead seek to influence others' thoughts about your own gameplay; this is a game of bluffing and informational maneuvering.
    
If you cannot decide on a DIALOGUE, you should respond with "ERROR: ..." with some explanation for why you cannot create a DIALOGUE.
"""
             ),
            ("user", "{input}")
        ])
        response_schemas = [
            ResponseSchema(name="dialogue", description="dialogue declaring your intent to act"),
            ResponseSchema(
                name="action", description="one of the LEGAL_ACTIONS matching your declared intent"
            ),
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        self.dialoguer = dialoguer_prompt | ChatOpenAI(
            openai_api_key=openai_api_key
        ) | output_parser  # | ActionDialogueExtractor

        reacter_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an AI-powered player in the game `The Resistance: Coup`.
Your name is {self.name}.
You must decide whether or not you want to react to the action another player is currently undertaking.

You will be given a detailed analysis (DETAILED_ANALYSIS) of the current state of the game.
You will also be given a list of legal actions (LEGAL_ACTIONS) to take.
You will also be given an ACTOR, which is the player who is currently acting.
You will also be given a CONVERSATION, which is a dialogue chain that has occurred between you and the other players during this round.

It is almost always an option to CHALLENGE, which means that you are guessing that the ACTOR is bluffing about their capacity to act (ACTION).  However, this is comes with a risk, because if you are wrong, you lose a card (of which you only have two, so CHALLENGE with a last card may lose the game entirely if wrong). 

You should RESPOND with internal dialogue text, which should be internal textual dialogue as thoughts, which contains some explanation of the move that you will make, and optionally, however seems relevant, some justification for this move (including lies, because bluffing and deception are an intimate part of the gameplay here).
    
If you cannot decide on a RATIONALE, you should respond with "ERROR: ..." with some explanation for why you cannot create a RATIONALE.
"""
             ),
            ("user", "{input}")
        ])

        self.reacter = reacter_prompt | ChatOpenAI(
            openai_api_key=openai_api_key
        ) | StrOutputParser()

    def analyze_state(self, game_state_summary):
        response = self.analyzer.invoke({"input": game_state_summary})
        return response

    def create_rationale(self, game_analysis: str, allowed_actions: List[str],
                         last_dialogue: Optional[List[str]] = None) -> Union[str, Dict, None]:
        response = self.rationalizer.invoke(
            {"input": f"```DETAILED_ANALYSIS:\r\n{game_analysis}\r\n\r\n```LEGAL_ACTIONS\r\n{allowed_actions}\r\n```"})
        return response

    def extract_choice(self, game_analysis: str, allowed_actions: List[str], rationale: str,
                       last_dialogue: Optional[List[str]] = None) -> Tuple[str, ActionType, Optional[str]]:
        response = self.dialoguer.invoke({
                                             "input": f"```DETAILED_ANALYSIS\r\n{game_analysis}```\r\n\r\n```LEGAL_ACTIONS\r\n{allowed_actions}\r\n```\r\n\r\n```RATIONALE\r\n{rationale}\r\n```"})
        return response['dialogue'], response['action'], response['target']

    def determine_reaction(self, game_analysis: str, allowed_actions: List[str], actor: str, conversation: List[str]) -> \
    Tuple[str, ActionType, Optional[str]]:
        reaction_rationale = self.reacter.invoke({
                                                     "input": f"```DETAILED_ANALYSIS\r\n{game_analysis}```\r\n\r\n```LEGAL_ACTIONS\r\n{allowed_actions}\r\n```\r\n\r\n```ACTOR\r\n{actor}\r\n```\r\n\r\n```CONVERSATION\r\n{conversation}\r\n```"})
        return self.extract_choice(game_analysis, allowed_actions, reaction_rationale)

# analyzer = AIGameAgent()
# game_state_summary = "Player A claimed Duke, Player B challenged and lost. Treasury contains 8 coins."
# analysis = analyzer.analyze_state(game_state_summary)
# print(analysis)
