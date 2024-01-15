import os
import random

from langchain_core.runnables import RunnableSerializable
from pydantic.dataclasses import dataclass
from typing import Optional, List, Dict, Union, Tuple

from src.models.action import ActionType
from src.models.agents.analysis_agent import create_game_state_analyzer, analyzer_template
from src.models.agents.card_discarder_agent import discarder_template, create_ai_card_discarder_agent
from src.models.agents.chatter_agent import create_ai_chatter_agent, chatter_template
from src.models.agents.chooser_agent import create_game_state_chooser, chooser_template
from src.models.agents.challenger_agent import create_game_state_challenger, \
    challenger_template
from src.models.agents.contester_chooser import create_game_state_contester_chooser, contester_chooser_template
from src.models.agents.rationalizer_agent import rationale_template, create_game_state_rationalizer
from src.models.agents.speech_redacter import create_game_speech_redacter, speech_redacter_template
from src.models.agents.speech_smoothener_agent import create_ai_speech_smoothing_agent, speech_smoothing_template
from src.models.traits import AICharacterTraits

openai_api_key = os.getenv("OPENAI_API_KEY")
from src.utils.logger import app_logger


class MyConfig:
    validate_assignment = False


@dataclass(config=MyConfig)
class AIGameAgent:
    name: str = "None"
    analyzer: RunnableSerializable = None
    rationalizer: RunnableSerializable = None
    challenger: RunnableSerializable = None
    chooser: RunnableSerializable = None
    contester_chooser: RunnableSerializable = None
    smoothener: RunnableSerializable = None
    chatter: RunnableSerializable = None
    redacter: RunnableSerializable = None
    discarder: RunnableSerializable = None
    traits: AICharacterTraits = None
    last_rationale: str = None

    def __init__(self, name: str):
        self.name = name

    def __post_init__(self):
        self.analyzer = create_game_state_analyzer(self.name)
        self.rationalizer = create_game_state_rationalizer(self.name)
        self.chooser = create_game_state_chooser(self.name)
        self.contester_chooser = create_game_state_contester_chooser(self.name)
        self.challenger = create_game_state_challenger(self.name)
        self.smoothener = create_ai_speech_smoothing_agent(self.name)
        self.chatter = create_ai_chatter_agent(self.name)
        self.redacter = create_game_speech_redacter(self.name)
        self.discarder = create_ai_card_discarder_agent(self.name)
        self.traits = AICharacterTraits()
        self.last_rationale = ""

    def analyze_state(self, game_state_summary, last_round_dialogue):
        app_logger.info(f"AI {self.name} analyzing state")
        message = {"input": analyzer_template(self.traits, game_state_summary, last_round_dialogue)}
        response = self.analyzer.invoke(message)
        app_logger.debug(f"Input Message: {message}\r\n\r\nResponse message: {response}")
        return response

    def _smoothen_speech(self, action: str, rationale: str, attempted_dialogue: str):
        app_logger.info(f"AI {self.name} Smoothening Speech to match its procedurally generated qualities")
        message = {"input": speech_smoothing_template(self.traits, action, rationale, attempted_dialogue)}
        response = self.smoothener.invoke(message)
        app_logger.debug(f"Input Message: {message}\r\n\r\nResponse message: {response}")
        return response

    def create_rationale(
            self,
            game_analysis: str,
            allowed_actions: List[str],
            last_dialogue: Optional[List[str]] = None,
    ) -> Union[str, Dict, None]:
        app_logger.info(f"AI {self.name} creating rationale")
        message = {
            "input": rationale_template(self.traits, game_analysis, allowed_actions, last_dialogue)
        }
        response = self.rationalizer.invoke(message)
        app_logger.debug(f"Input Message: {message}\r\n\r\nResponse message: {response}")
        self.last_rationale = response
        return response

    def extract_choice(
            self,
            game_analysis: str,
            allowed_actions: List[str],
            rationale: str,
            last_dialogue: Optional[List[str]] = None,
    ) -> Tuple[str, Optional[str], Optional[str]]:
        extracted_response: Optional[Tuple[ActionType, Optional[str], Optional[str]]] = None
        while extracted_response is None:
            try:
                app_logger.info(f"AI {self.name} extracting choice")
                message = {
                    "input": chooser_template(self.traits, game_analysis, allowed_actions, rationale, last_dialogue)
                }
                extracted_response = self.chooser.invoke(message)
                app_logger.debug(f"Input Message: {message}\r\n\r\nResponse message: {extracted_response}")

            except Exception as e:
                if "Got invalid JSON object." not in f"{e}":
                    app_logger.warn(f"Received retryable error: {e}")
                else:
                    app_logger.debug(f"AI {self.name} failed to extract choice with error {e}")

        action: str = extracted_response["action"]

        speech: Optional[str] = "None"
        if extracted_response["dialogue"] is not None and extracted_response["dialogue"] != "None":
            speech = self._smoothen_speech(extracted_response["action"], rationale, extracted_response["dialogue"])

        target: Optional[str] = None
        if extracted_response["target"] is not None:
            if extracted_response["target"] != "None":
                target = extracted_response["target"]

        app_logger.info(f"AI {self.name} redacting speech")
        message = {
            "input": speech_redacter_template(
                self.traits,
                "None" if action is None or action.lower() == "None" else action,
                rationale,
                speech
            )
        }
        speech = self.redacter.invoke(message)
        app_logger.debug(f"Input Message: {message}\r\n\r\nResponse message: {speech}")

        return (
            action,
            speech,
            target
        )

    def extract_contest_choice(
            self,
            game_analysis: str,
            actor: str,
            target: Optional[str],
            allowed_actions: List[str],
            rationale: str,
            last_dialogue: Optional[List[str]] = None,
    ) -> Tuple[str, Optional[str], Optional[str]]:
        extracted_response: Optional[Tuple[ActionType, Optional[str], Optional[str]]] = None
        while extracted_response is None:
            try:
                app_logger.info(f"AI {self.name} extracting CONTEST choice")
                message = {
                    "input": contester_chooser_template(self.traits, game_analysis, actor, target, allowed_actions, rationale, last_dialogue)
                }
                extracted_response = self.contester_chooser.invoke(message)
                app_logger.debug(f"Input Message: {message}\r\n\r\nResponse message: {extracted_response}")

            except Exception as e:
                if "Got invalid JSON object." not in f"{e}":
                    app_logger.warn(f"Received retryable error: {e}")
                else:
                    app_logger.debug(f"AI {self.name} failed to extract choice with error {e}")

        action: str = extracted_response["action"]

        speech: Optional[str] = "None"
        if extracted_response["dialogue"] is not None and extracted_response["dialogue"] != "None":
            speech = self._smoothen_speech(extracted_response["action"], rationale, extracted_response["dialogue"])

        target: Optional[str] = None
        if extracted_response["target"] is not None:
            if extracted_response["target"] != "None":
                target = extracted_response["target"]

        app_logger.info(f"AI {self.name} redacting speech")
        message = {
            "input": speech_redacter_template(
                self.traits,
                "None" if action is None or action.lower() == "None" else action,
                rationale,
                speech
            )
        }
        speech = self.redacter.invoke(message)
        app_logger.debug(f"Input Message: {message}\r\n\r\nResponse message: {speech}")

        return (
            action,
            speech,
            target
        )

    def determine_challenge_reaction(
            self, 
            game_analysis: str, 
            actor: str, 
            target: Optional[str], 
            conversation: List[str]
    ) -> Tuple[str, Optional[str], Optional[str]]:
        challenge_rationale: Optional[str] = None
        while challenge_rationale is None:
            try:
                app_logger.info(f"AI {self.name} determining challenge reaction")
                message = {
                    "input": challenger_template(self.traits, game_analysis, actor, target, conversation)
                }
                challenge_rationale = self.challenger.invoke(message)
                app_logger.debug(f"Input Message: {message}\r\n\r\nResponse message: {challenge_rationale}")
            except Exception as e:
                app_logger.warn(e)

        return self.extract_contest_choice(
            game_analysis,
            actor,
            target,
            ["Challenge", "None"],
            challenge_rationale,
            conversation
        )

    def determine_block_reaction(
            self,
            game_analysis: str,
            actor: str,
            cards: List[str],
            target: Optional[str],
            conversation: List[str]
    ) -> Tuple[str, Optional[str], Optional[str]]:
        block_rationale: Optional[str] = None
        while block_rationale is None:
            try:
                app_logger.info(f"AI {self.name} determining block reaction")
                message = {
                    "input": challenger_template(self.traits, game_analysis, actor, target, conversation)
                }
                block_rationale = self.challenger.invoke(message)
                app_logger.debug(f"Input Message: {message}\r\n\r\nResponse message: {block_rationale}")
            except Exception as e:
                app_logger.warn(e)
        return self.extract_contest_choice(
            game_analysis,
            actor,
            target,
            ["Block", "None"],
            block_rationale,
            conversation
        )

    def check_chat(self, modifier: float = 1):
        return (self.traits.chattiness * modifier) > random.random()

    def chat(
            self,
            actor: str,
            event_to_chat_about: str,
            past_events=list[str]
    ) -> str:
        speech: Optional[str] = None
        while speech is None:
            try:
                app_logger.info(f"AI {self.name} chatting")
                message = {
                    "input": chatter_template(
                        traits=self.traits,
                        event_to_chat_about=event_to_chat_about,
                        past_events=past_events,
                        last_rationale=self.last_rationale
                    )
                }
                unsmoothened_speech = self.chatter.invoke(message)
                app_logger.debug(f"Input Message: {message}\r\n\r\nResponse message: {unsmoothened_speech}")
                speech = self._smoothen_speech(
                    action="Chat",
                    rationale=self.last_rationale,
                    attempted_dialogue=unsmoothened_speech
                )
            except Exception as e:
                app_logger.warn(e)
        return speech

    def discard(
            self,
            past_events: List[str],
            cards: List[str]
    ) -> str:
        target_card: Optional[str] = None
        while target_card is None:
            try:
                app_logger.info(f"AI {self.name} discarding from {cards}")
                message = {
                    "input": discarder_template(
                        traits=self.traits,
                        past_events=past_events,
                        last_rationale=self.last_rationale,
                        cards=cards
                    )
                }
                target_card = self.discarder.invoke(message)
                app_logger.debug(f"Input Message: {message}\r\n\r\nResponse message: {target_card}")
            except Exception as e:
                app_logger.warn(e)
        return target_card
