import os
import random

from langchain_core.runnables import RunnableSerializable
from pydantic.dataclasses import dataclass
from typing import Optional, List, Dict, Union, Tuple

from src.models.action import ActionType
from src.models.agents.analysis_agent import create_game_state_analyzer, analyzer_template
from src.models.agents.chooser_agent import create_game_state_chooser, chooser_template
from src.models.agents.challenger_agent import create_game_state_challenger, \
    challenger_template
from src.models.agents.rationalizer_agent import rationale_template, create_game_state_rationalizer
from src.models.traits import AICharacterTraits

openai_api_key = os.getenv("OPENAI_API_KEY")


class MyConfig:
    validate_assignment = False


@dataclass(config=MyConfig)
class AIGameAgent:
    name: str = "None"
    analyzer: RunnableSerializable = None
    rationalizer: RunnableSerializable = None
    challenger: RunnableSerializable = None
    chooser: RunnableSerializable = None
    traits: AICharacterTraits = None

    def __init__(self, name: str):
        self.name = name
    def __post_init__(self):
        self.analyzer = create_game_state_analyzer(self.name)
        self.rationalizer = create_game_state_rationalizer(self.name)
        self.chooser = create_game_state_chooser(self.name)
        self.challenger = create_game_state_challenger(self.name)
        self.traits = AICharacterTraits()

    def analyze_state(self, game_state_summary, last_round_dialogue):
        response = self.analyzer.invoke({"input": analyzer_template(self.traits, game_state_summary, last_round_dialogue)})
        return response

    def create_rationale(
        self,
        game_analysis: str,
        allowed_actions: List[str],
        last_dialogue: Optional[List[str]] = None,
    ) -> Union[str, Dict, None]:
        response = self.rationalizer.invoke(
            {
                "input": rationale_template(self.traits, game_analysis, allowed_actions, last_dialogue)
            }
        )
        return response

    def extract_choice(
        self,
        game_analysis: str,
        allowed_actions: List[str],
        rationale: str,
        last_dialogue: Optional[List[str]] = None,
    ) -> Tuple[str, ActionType, Optional[str]]:
        extracted_response: Union[Tuple[str, ActionType, Optional[str]], None] = None
        while extracted_response is None:
            try:
                extracted_response = self.chooser.invoke(
                    {
                        "input": chooser_template(self.traits, game_analysis, allowed_actions, rationale, last_dialogue)
                    }
                )
            except Exception as e:
                if "Got invalid JSON object." not in f"{e}":
                    print(e)

        target: Optional[str] = None
        if extracted_response["target"] is not None:
            if extracted_response["target"] != "None":
                target = extracted_response["target"]
        return (
            extracted_response["dialogue"],
            extracted_response["action"],
            target
        )

    def determine_challenge_reaction(
        self, game_analysis: str, actor: str, target: Optional[str], conversation: List[str]
    ) -> Tuple[str, ActionType, Optional[str]]:
        challenge_rationale: Union[str, None] = None
        while challenge_rationale is None:
            try:
                challenge_rationale = self.challenger.invoke(
                    {
                        "input": challenger_template(self.traits, game_analysis, actor, target, conversation)
                    }
                )
                extracted_choices: Union[Tuple[str, ActionType, Optional[str]], None] = None
                while extracted_choices is None:
                    try:
                        extracted_choices = self.extract_choice(
                            game_analysis, ["Challenge", "None"], challenge_rationale
                        )
                    except Exception as e:
                        print(e)
                return extracted_choices
            except Exception as e:
                if "Got invalid JSON object." not in f"{e}":
                    print(e)

    def _check_chat(self):
        if (random.random() * self.traits.chattiness) > 0.5:
            return True
        else:
            return False

    ## Let's wire up a way for these folks to vibe
    # def maybe_comment(
    #         self,
    #         game_analysis: str,
    #         game_rationale: str,
    #         actor: str,
    #         target: Optional[str],
    #         conversation: List[str]
    # ) -> Tuple[str, ActionType, Optional[str]]: