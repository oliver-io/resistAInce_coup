from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Union
from src.models.agents.ai_orchestrator import AIGameAgent

from pydantic import BaseModel

from src.models.action import (
    Action,
    ActionType,
    AssassinateAction,
    CounterAction,
    CoupAction,
    ExchangeAction,
    ForeignAidAction,
    IncomeAction,
    StealAction,
    TaxAction,
)
from src.models.card import Card, CardType


class BasePlayer(BaseModel, ABC):
    name: str
    ai_agent: AIGameAgent
    coins: int = 0
    cards: List[Card] = []
    is_ai: bool
    is_active: bool = False

    def __str__(self):
        return f"{self.name}"

    def reset_player(self):
        self.coins = 0
        self.cards = []

    def _validate_action(self, action: Action, target_player: Optional["BasePlayer"]):
        if not target_player:
            return True

        # Can't steal from player with 0 coins
        if action.action_type == ActionType.steal and target_player.coins == 0:
            return False

        return True

    def available_actions(self) -> List[Action]:
        # You must coup if you have more than 10 coins
        if self.coins >= 10:
            return [CoupAction()]

        actions = [IncomeAction(), ForeignAidAction(), TaxAction(), StealAction(), ExchangeAction()]
        if self.coins >= 7:
            actions.append(CoupAction())

        if self.coins >= 3:
            actions.append(AssassinateAction())

        return actions

    def find_card(self, card_type: CardType) -> Optional[Card]:
        for ind, card in enumerate(self.cards):
            if card.card_type == card_type:
                return self.cards.pop(ind)

        return None

    @abstractmethod
    def choose_action(
        self,
        other_players: List["BasePlayer"],
        state: str,
        last_round_dialogue: Optional[List[str]] = None,
    ) -> Tuple[Action, Optional["BasePlayer"], Optional[str]]:
        """Choose the next action to perform"""
        pass

    @abstractmethod
    def determine_challenge(
        self,
        actor: "BasePlayer",
        target_player: Union["BasePlayer", None],
        action: Union[Action, CounterAction],
        state: str,
        dialogue_so_far: Optional[List[str]],
    ) -> Tuple[bool, Optional[str]]:
        """Choose whether to challenge the current player"""
        pass

    @abstractmethod
    def determine_chat(
        self,
        actor: "BasePlayer",
        event_to_chat_about: str,
        past_events: Optional[List[str]],
        modifier: Optional[float],
    ) -> Optional[str]:
        """Choose whether to chat about the current event"""
        pass

    @abstractmethod
    def determine_counter(
        self,
        actor: "BasePlayer",
        target_player: Optional["BasePlayer"],
        action: Union[Action, CounterAction],
        state: str,
        dialogue_so_far: Optional[List[str]],
    ) -> Tuple[bool, Optional[str]]:
        """Choose whether to counter the current player's action"""
        pass

    @abstractmethod
    def remove_card(self, past_events: List[str]) -> str:
        """Choose a card and remove it from your hand"""
        pass

    @abstractmethod
    def choose_exchange_cards(
        self, exchange_cards: list[Card], current_events: List[str]
    ) -> Tuple[Card, Card]:
        """Perform the exchange action. Pick which 2 cards to send back to the deck"""
        pass
