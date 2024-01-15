import random
import time
from typing import List, Optional, Tuple, Union

from src.models.action import Action, get_counter_action, CounterAction
from src.models.card import Card
from src.models.players.base import BasePlayer
from src.utils.print import print_text, print_texts
from src.utils.logger import app_logger

CHALLENGE_CONSTANT = 0.5


class AIPlayer(BasePlayer):
    is_ai: bool = True

    def choose_action(
            self,
            other_players: List[BasePlayer],
            state: str,
            last_round_dialogue: Optional[List[str]] = None
    ) -> Tuple[Action, Optional[BasePlayer], Optional[str]]:
        """Choose the next action to perform"""

        available_actions = self.available_actions()
        print_text(f"[bold magenta]{self}[/] is thinking about their move...", with_markup=True)

        chosen_action: Optional[Action] = None
        extracted_target: Optional[str] = None
        extracted_action: Optional[str] = None
        while chosen_action is None:
            try:
                analysis = self.ai_agent.analyze_state(state, last_round_dialogue)

                rationale = self.ai_agent.create_rationale(
                    analysis, [action.action_type for action in available_actions]
                )

                print_text(f'{self.name} thinks "[bold cyan]{rationale}[/]"', with_markup=True)

                extracted_action, extracted_speech, extracted_target = self.ai_agent.extract_choice(
                    analysis, [action.action_type for action in available_actions], rationale
                )

                # Which (if any) action matches the model output?
                chosen_action: Union[Action, None] = None
                for action in available_actions:
                    if action.action_type == extracted_action:
                        chosen_action = action

                if chosen_action is None:
                    available_actions_str = ", ".join([action.action_type for action in available_actions])
                    app_logger.error(f"Bad action choice {chosen_action} for available actions")
                    app_logger.error(f"Available actions: {available_actions_str}")
                    app_logger.error(f"Extracted action: {extracted_action}")
                    app_logger.error(f"Extracted speech: {extracted_speech}")
                    app_logger.error(f"Extracted target: {extracted_target}")
                    raise RuntimeError("The agent did not choose a valid action")

            except Exception as e:
                app_logger.error(f"Bad action choice {chosen_action} for available actions")
                app_logger.error(e)

        # Let's spare OpenAI the parsing of markup in speech:
        headless_speech: str = ""

        # Which (if any) target matches the model output?\
        if extracted_target == "None":
            extracted_target = None

        if extracted_target is None:
            headless_speech = f'{self.name} says "[{extracted_speech}"'
            print_text(f'{self.name} says "[bold yellow]{extracted_speech}[/]"', with_markup=True)
        else:
            headless_speech = f'{self.name} says to {extracted_target} "[{extracted_speech}"'
            print_text(
                f'{self.name} says to {extracted_target}, "[bold yellow]{extracted_speech}[/]"',
                with_markup=True,
            )

        time.sleep(1)

        # Coup is only option
        if len(available_actions) == 1:
            if extracted_action != "Coup":
                raise pydantic.ValidationError(
                    "Only coup is available, but the agent did not choose coup"
                )
            elif extracted_target is None:
                raise pydantic.ValidationError(
                    "Only coup is available, but the agent did not choose a target"
                )

        chosen_target: Optional[BasePlayer] = None
        if extracted_target is not None:
            for player in other_players:
                if player.name == extracted_target:
                    chosen_target = player

        return chosen_action, chosen_target, headless_speech

    def determine_challenge(
            self,
            actor: BasePlayer,
            target_player: Optional["BasePlayer"],
            action: Union[Action, CounterAction],
            state: str,
            dialogue_so_far: Optional[List[str]],
    ) -> Tuple[bool, Optional[str]]:
        """Choose whether to challenge the current player"""
        if target_player is None:
            # Todo: chat?
            print_text(
                f"[bold magenta]{self}[/] is considering challenging {actor}'s use of {action}...",
                with_markup=True,
            )
        else:
            target_string = target_player.name if target_player is not self else "themselves"
            print_text(
                f"[bold magenta]{self}[/] is considering challenging {actor}'s use of {action} against {target_string}...",
                with_markup=True,
            )
        analysis = self.ai_agent.analyze_state(state, dialogue_so_far)

        action, dialogue, maybe_target = self.ai_agent.determine_challenge_reaction(
            analysis,
            actor.name,
            target_player.name if target_player is not None else None,
            dialogue_so_far,
        )

        if self.ai_agent.check_chat():
            headless_speech = f'{self.name} says "{dialogue}"'
            print_text(f'{self.name} says "[bold yellow]{dialogue}[/]"', with_markup=True)
        else:
            headless_speech = None

        return (action == "Challenge"), headless_speech

    def determine_counter(
            self,
            actor: BasePlayer,
            target_player: Optional["BasePlayer"],
            action: Action,
            state: str,
            dialogue_so_far: Optional[List[str]],
    ) -> Tuple[bool, Optional[str]]:
        """Choose whether to counter/block the current player's action"""
        if target_player is None:
            # Todo: chat?
            print_text(
                f"[bold magenta]{self}[/] is considering blocking {actor}'s use of {action}...",
                with_markup=True,
            )
        else:
            target_string = target_player.name if target_player is not self else "themselves"
            print_text(
                f"[bold magenta]{self}[/] is considering blocking {actor}'s use of {action} against {target_string}...",
                with_markup=True,
            )
        analysis = self.ai_agent.analyze_state(state, dialogue_so_far)

        action, dialogue, _ = self.ai_agent.determine_block_reaction(
            game_analysis=analysis,
            actor=actor.name,
            cards=[f"{card}" for card in enumerate(self.cards)],
            target=target_player.name if target_player is not None else None,
            conversation=dialogue_so_far,
        )

        headless_speech = f'{self.name} says "{dialogue}"'
        print_text(f'{self.name} says "[bold yellow]{dialogue}[/]"', with_markup=True)

        return (action == "Block"), headless_speech

    def determine_chat(
            self,
            actor: "BasePlayer",
            event_to_chat_about: str,
            past_events: Optional[List[str]],
            modifier: Optional[float] = 1
    ) -> Optional[str]:
        """Choose whether to chat about the current event"""
        if self.ai_agent.check_chat():
            speech = self.ai_agent.chat(
                actor=actor,
                event_to_chat_about=event_to_chat_about,
                past_events=past_events
            )

            headless_speech = f'{self.name} says "{speech}"'
            print_text(f'{self.name} says "[bold yellow]{speech}[/]"', with_markup=True)
            return headless_speech

        return None

    def remove_card(self, past_events: List[str]) -> str:
        """Choose a card and remove it from your hand"""
        target_card: Optional[Card] = None
        while target_card is None:
            target_discard = self.ai_agent.discard(
                cards=[f"{card}" for card in self.cards],
                past_events=past_events,
            )

            for possible_target in self.cards:
                app_logger.debug(f"Comparing: {str(possible_target).lower()}, {target_discard.lower()}")
                if str(possible_target).lower() == target_discard.lower():
                    target_card = possible_target
                    break
            if target_card is None:
                app_logger.warn(f"AI {self.name} tried to discard {target_discard}, but they don't have that card")

        # TODO: run this through the chooser model, should work with fake actions like "DISCARD_ASSASSIN"
        # Remove a random card
        discarded_card = self.cards.pop(random.randrange(len(self.cards)))
        print_texts(f"{self} discards their ", (f"{discarded_card}", discarded_card.style), " card")
        return f"{discarded_card}"

    def choose_exchange_cards(self, exchange_cards: list[Card], past_events: List[str]) -> Tuple[Card, Card]:
        """Perform the exchange action. Pick which 2 cards to send back to the deck"""
        # TODO: seems like this probably needs its own agent
        self.cards += exchange_cards
        random.shuffle(self.cards)

        print_text(f"{self} is thinking about which cards to discard...")
        target_card_a: Optional[Card] = None
        while target_card_a is None:
            target_discard = self.ai_agent.discard(
                cards=[f"{card}" for card in self.cards],
                past_events=past_events,
            )
            for possible_target in self.cards:
                if str(possible_target).lower() == target_discard.lower():
                    target_card_a = possible_target
                    break
            if target_card_a is None:
                app_logger.warn(f"AI {self.name} tried to discard {target_discard} (1), but they don't have that card")

        discard_a = self.cards.pop(self.cards.index(target_card_a))

        target_card_b: Optional[Card] = None
        while target_card_b is None:
            target_discard = self.ai_agent.discard(
                cards=[f"{card}" for card in self.cards],
                past_events=past_events,
            )
            for possible_target in self.cards:
                if str(possible_target).lower() == target_discard.lower():
                    target_card_b = possible_target
                    break
            if target_card_b is None:
                app_logger.warn(f"AI {self.name} tried to discard {target_discard} (2), but they don't have that card")

        print_text(f"{self} exchanges 2 cards")
        return discard_a, self.cards.pop(self.cards.index(target_card_b))
