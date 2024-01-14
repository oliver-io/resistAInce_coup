import random
import time
from typing import List, Optional, Tuple, Union

from src.models.action import Action, get_counter_action, CounterAction
from src.models.card import Card
from src.models.players.base import BasePlayer
from src.utils.print import print_text, print_texts

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

        analysis = self.ai_agent.analyze_state(state, last_round_dialogue)

        rationale = self.ai_agent.create_rationale(
            analysis, [action.action_type for action in available_actions]
        )

        print_text(f'{self.name} thinks "[bold cyan]{rationale}[/]"', with_markup=True)

        extracted_speech, extracted_action, extracted_target = self.ai_agent.extract_choice(
            analysis, [action.action_type for action in available_actions], rationale
        )


        # Which (if any) action matches the model output?
        chosen_action: Union[Action, None] = None
        for action in available_actions:
            if action.action_type == extracted_action:
                chosen_action = action

        if chosen_action is None:
            raise RuntimeError("The agent did not choose a valid action")

        # Let's spare OpenAI the parsing of markup in speech:
        headless_speech: str = ""

        # Which (if any) target matches the model output?\
        if extracted_target == "None":
            extracted_target = None

        if extracted_target is not None:
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
        target_player: BasePlayer,
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

        dialogue, action, _ = self.ai_agent.determine_challenge_reaction(
            analysis,
            actor.name,
            target_player.name if target_player is not None else None,
            dialogue_so_far,
        )

        headless_speech = f'{self.name} says "{dialogue}"'
        print_text(f'{self.name} says "[bold yellow]{dialogue}[/]"', with_markup=True)

        return (action == "Challenge"), headless_speech

    def determine_counter(self, player: BasePlayer) -> bool:
        """Choose whether to counter the current player's action"""

        # TODO: I think we can actually just use the "challenge" model with a little bit of tweaking
        # 10% chance of countering
        return random.randint(0, 9) == 0

    def remove_card(self) -> str:
        """Choose a card and remove it from your hand"""

        # TODO: run this through the chooser model, should work with fake actions like "DISCARD_ASSASSIN"
        # Remove a random card
        discarded_card = self.cards.pop(random.randrange(len(self.cards)))
        print_texts(f"{self} discards their ", (f"{discarded_card}", discarded_card.style), " card")
        return f"{discarded_card}"

    def choose_exchange_cards(self, exchange_cards: list[Card]) -> Tuple[Card, Card]:
        """Perform the exchange action. Pick which 2 cards to send back to the deck"""

        # TODO: seems like this probably needs its own agent
        self.cards += exchange_cards
        random.shuffle(self.cards)
        print_text(f"{self} exchanges 2 cards")

        return self.cards.pop(), self.cards.pop()
