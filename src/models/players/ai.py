import random
import time
from typing import List, Optional, Tuple, Union

from src.models.action import Action
from src.models.card import Card
from src.models.players.base import BasePlayer
from src.utils.print import print_text, print_texts


class AIPlayer(BasePlayer):
    is_ai: bool = True

    def choose_action(self, other_players: List[BasePlayer], state: str) -> Tuple[Action, Optional[BasePlayer]]:
        """Choose the next action to perform"""

        available_actions = self.available_actions()

        print("ENGAGING ANALYSIS AGENT")
        analysis = self.ai_agent.analyze_state(state)
        print("ANALYSIS AGENT COMPLETE")
        print(analysis)

        print("ENGAGING RATIONALIZER AGENT")
        rationale = self.ai_agent.create_rationale(analysis, [action.action_type for action in available_actions])
        print("ANALYSIS RATIONALIZER COMPLETE")
        print_text(f"{self.name} thinks \"[bold cyan]{rationale}[/]\"", with_markup=True)

        print("ENGAGING EXTRACTION AGENT")
        extracted_speech, extracted_action, extracted_target = self.ai_agent.extract_choice(
            analysis,
            [action.action_type for action in available_actions],
            rationale
        )
        print("ANALYSIS SPEECH COMPLETE")
        print(f"Extracted action & target: {extracted_action}, {extracted_target}")

        chosen_action: Union[Action, None] = None
        for action in available_actions:
            if action.action_type == extracted_action:
                chosen_action = action

        if chosen_action is None:
            raise RuntimeError("The agent did not choose a valid action")

        headless_speech:str = '';

        if extracted_target is not None:
            headless_speech = f"{self.name} says \"[{extracted_speech}\""
            print_text(f"{self.name} says \"[bold yellow]{extracted_speech}[/]\"", with_markup=True)
        else:
            headless_speech = f"{self.name} says to {extracted_target} \"[{extracted_speech}\""
            print_text(f"{self.name} says to {extracted_target}, \"[bold yellow]{extracted_speech}[/]\"",
                       with_markup=True)

        print_text(f"[bold magenta]{self}[/] is thinking...", with_markup=True)
        time.sleep(1)

        # Coup is only option
        if len(available_actions) == 1:
            player = random.choice(other_players)
            return available_actions[0], player

        # Pick any other random choice (might be a bluff)
        target_action = random.choice(available_actions)
        target_player = None

        if target_action.requires_target:
            target_player = random.choice(other_players)

        # Make sure we have a valid action/player combination
        while not self._validate_action(target_action, target_player):
            target_action = random.choice(available_actions)
            if target_action.requires_target:
                target_player = random.choice(other_players)

        return target_action, target_player, headless_speech

    def determine_challenge(self, player: BasePlayer) -> bool:
        """Choose whether to challenge the current player"""

        # 20% chance of challenging
        return random.randint(0, 4) == 0

    def determine_counter(self, player: BasePlayer) -> bool:
        """Choose whether to counter the current player's action"""

        # 10% chance of countering
        return random.randint(0, 9) == 0

    def remove_card(self) -> None:
        """Choose a card and remove it from your hand"""

        # Remove a random card
        discarded_card = self.cards.pop(random.randrange(len(self.cards)))
        print_texts(f"{self} discards their ", (f"{discarded_card}", discarded_card.style), " card")

    def choose_exchange_cards(self, exchange_cards: list[Card]) -> Tuple[Card, Card]:
        """Perform the exchange action. Pick which 2 cards to send back to the deck"""

        self.cards += exchange_cards
        random.shuffle(self.cards)
        print_text(f"{self} exchanges 2 cards")

        return self.cards.pop(), self.cards.pop()
