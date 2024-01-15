import random
import time
from enum import Enum
from typing import List, Optional, Tuple, Union

import names
from rich.console import Console
from src.models.agents.ai_orchestrator import AIGameAgent

from src.models.action import Action, ActionType, CounterAction, get_counter_action
from src.models.card import Card, build_deck
from src.models.players.ai import AIPlayer
from src.models.players.base import BasePlayer
from src.models.players.human import HumanPlayer
from src.utils.game_state import generate_players_table, generate_state_panel
from src.utils.print import (
    build_action_report_string,
    build_counter_report_string,
    print_confirm,
    print_panel,
    print_table,
    print_text,
    print_texts,
)


class ChallengeResult(Enum):
    no_challenge = 0
    challenge_failed = 1
    challenge_succeeded = 2


class ResistanceCoupGameHandler:
    _players: List[BasePlayer] = []
    _current_player_index = 0
    _deck: List[Card] = []
    _discard: List[str] = []
    _number_of_players: int = 0
    _treasury: int = 0
    _current_round_events: List[str] = []
    _last_round_events: List[str] = []

    def __init__(self, player_name: str, number_of_players: int):
        self._number_of_players = number_of_players

        # Set up players
        # self._players.append(HumanPlayer(name=player_name))

        unique_names = set()
        for i in range(number_of_players):
            gender = random.choice(["male", "female"])

            ai_name = names.get_first_name(gender=gender)
            while ai_name in unique_names:
                ai_name = names.get_first_name(gender=gender)

            unique_names.add(ai_name)

            self._players.append(AIPlayer(name=ai_name, ai_agent=AIGameAgent(name=ai_name)))

        print_text(f"\r\n\t[bold magenta]The Playbill![/]", with_markup=True)
        time.sleep(1)
        for player in self._players:
            print_text(f"\t\t[bold cyan]{player}[/]: ", with_markup=True)
            print_text(f"\tPersonality seed: 'You {player.ai_agent.traits.personality_trait}'", with_markup=True)
            print_text(f"\tRationality seed: 'You are {player.ai_agent.traits.rationalization_trait}'", with_markup=True)
            print_text(f"\tSpeechiness seed: 'You {player.ai_agent.traits.speech_trait}'", with_markup=True)
            time.sleep(1)


    @property
    def current_player(self) -> BasePlayer:
        return self._players[self._current_player_index]

    @property
    def remaining_player(self) -> BasePlayer:
        """Return the only remaining player"""
        return [player for player in self._players if player.is_active][0]

    def _broadcast_and_record(self, msg: str):
        print_text(msg)
        self._current_round_events.append(msg)

    def print_game_state(self) -> None:
        print_table(generate_players_table(self._players, self._current_player_index))
        print_panel(
            generate_state_panel(self._deck, self._treasury, self.current_player, self._discard)
        )

    def _players_without_player(self, excluded_player: BasePlayer):
        players_copy = self._players.copy()
        return [
            player
            for player in players_copy
            if player.is_active and player.name != excluded_player.name
        ]

    def _shuffle_deck(self) -> None:
        random.shuffle(self._deck)

    def setup_game(self) -> None:
        self._deck = build_deck()
        self._shuffle_deck()

        self._treasury = 50 - 2 * len(self._players)

        for player in self._players:
            player.reset_player()

            # Deal 2 cards to each player
            player.cards.append(self._deck.pop())
            player.cards.append(self._deck.pop())

            # Gives each player 2 coins
            player.coins = 2

            # Includes the player in the game
            player.is_active = True

        # Random starting player
        self._current_player_index = random.randint(0, self._number_of_players - 1)

    def _swap_card(self, player: BasePlayer, card: Card) -> None:
        self._deck.append(card)
        self._shuffle_deck()
        player.cards.append(self._deck.pop())

    def _take_coin_from_treasury(self, player: BasePlayer, number_of_coins: int):
        if number_of_coins <= self._treasury:
            self._treasury -= number_of_coins
            player.coins += number_of_coins
        else:
            coins = self._treasury
            self._treasury = 0
            player.coins += coins

    def _give_coin_to_treasury(self, player: BasePlayer, number_of_coins: int):
        self._treasury += number_of_coins
        player.coins -= number_of_coins

    def _next_player(self):
        self._current_player_index = (self._current_player_index + 1) % len(self._players)
        while not self.current_player.is_active:
            self._current_player_index = (self._current_player_index + 1) % len(self._players)

    def _remove_defeated_player(self) -> Optional[BasePlayer]:
        for ind, player in enumerate(self._players):
            if not player.cards and player.is_active:
                player.is_active = False
                self._give_coin_to_treasury(player, player.coins)

                return player
        return None

    def _determine_win_state(self) -> bool:
        return sum(player.is_active for player in self._players) == 1

    def _build_headless_state(self, current_player: BasePlayer) -> str:
        player_table_text = generate_players_table(
            self._players, self._players.index(current_player)
        )
        state_table_text = generate_state_panel(
            self._deck, self._treasury, current_player, self._discard
        )
        console = Console()
        with console.capture() as capture:
            console.print(player_table_text)
            console.print(state_table_text)
        str_output = capture.get()
        summary = f"```GAMESTATE\n\n{str_output}```"
        return summary

    def _action_phase(self) -> Tuple[Action, Optional[BasePlayer], Optional[str]]:
        summary = self._build_headless_state(self._players[self._current_player_index])
        target_action, target_player, speech = self.current_player.choose_action(
            self._players_without_player(self.current_player), summary, self._last_round_events
        )
        print_text(
            build_action_report_string(
                player=self.current_player, action=target_action, target_player=target_player
            ),
            with_markup=True,
        )

        return target_action, target_player, speech

    def _challenge_against_player_failed(
            self,
            player_being_challenged: BasePlayer,
            card: Card,
            challenger: BasePlayer
    ):
        # Player being challenged reveals the card
        print_texts(f"{player_being_challenged} reveals their ", (f"{card}", card.style), " card!")
        self._current_round_events.append(f"{player_being_challenged} reveals their {card} card!")

        self._broadcast_and_record(f"{challenger} loses the challenge")
        chat = challenger.determine_chat(
            actor=challenger,
            event_to_chat_about=f"You predicted {player_being_challenged} was bluffing, but you were wrong",
            past_events=self._current_round_events,
            modifier=1.2
        )

        if chat is not None:
            self._current_round_events.append(chat)

        # Challenge player loses influence (chooses a card to remove)
        self._discard.append(challenger.remove_card(self._current_round_events))

        # Player puts card into the deck and gets a new card
        self._swap_card(player_being_challenged, card)
        self._broadcast_and_record(f"{player_being_challenged} gets a new card")

        for player in self._players_without_player(challenger):
            chat = player.determine_chat(
                actor=challenger,
                event_to_chat_about=f"{challenger} challenged {player_being_challenged} and lost a card",
                past_events=self._current_round_events,
                modifier=.8
            )
            if chat is not None:
                self._current_round_events.append(chat)

    def _challenge_against_player_succeeded(self, player_being_challenged: BasePlayer):
        message = f"{player_being_challenged} was caught bluffing! They do not have the required card!"
        print_text(message)
        self._current_round_events.append(message)

        chat = player_being_challenged.determine_chat(
            actor=player_being_challenged,
            event_to_chat_about="You were caught bluffing! You do not have the required card and will lose one!",
            past_events=self._current_round_events,
            modifier=1.2
        )

        if chat is not None:
            self._current_round_events.append(chat)

        for player in self._players_without_player(player_being_challenged):
            chat = player.determine_chat(
                actor=player_being_challenged,
                event_to_chat_about=f"{player_being_challenged} was caught bluffing! They do not have the required card!",
                past_events=self._current_round_events,
                modifier=.8
            )

            if chat is not None:
                self._current_round_events.append(chat)

        # Player being challenged loses influence (chooses a card to remove)
        self._discard.append(player_being_challenged.remove_card(self._current_round_events))

    def _challenge_phase(
            self,
            other_players: list[BasePlayer],
            player_being_challenged: BasePlayer,
            action_being_challenged: Union[Action, CounterAction],
            dialogue_so_far: Optional[List[str]] = None,
            action_target: BasePlayer = None,
    ) -> Tuple[ChallengeResult, Optional[List[str]]]:
        accumulated_speech = []

        # Every player can choose to challenge, but let's start with the player targeted:
        traversal_order: List[int] = []
        if action_target is not None:
            traversal_order = [self._players.index(action_target)]
            for player in other_players:
                if player is not action_target and player is not player_being_challenged:
                    traversal_order.append(self._players.index(player))
        else:
            for player in other_players:
                if player is not player_being_challenged:
                    traversal_order.append(self._players.index(player))

        for i in traversal_order:
            challenger = self._players[i]
            should_challenge, challenge_speech = challenger.determine_challenge(
                player_being_challenged,
                action_target,
                action_being_challenged,
                self._build_headless_state(challenger),
                dialogue_so_far,
            )
            if challenge_speech is not None:
                accumulated_speech.append(challenge_speech)

            if should_challenge:
                message = f"{challenger} is challenging {player_being_challenged}!"
                print_text(message)
                self._current_round_events.append(message)

                # Player being challenged has the card
                if card := player_being_challenged.find_card(
                        action_being_challenged.associated_card_type
                ):
                    self._challenge_against_player_failed(
                        player_being_challenged=player_being_challenged,
                        card=card,
                        challenger=challenger,
                    )
                    return ChallengeResult.challenge_failed, accumulated_speech

                # Player being challenged bluffed
                else:
                    self._challenge_against_player_succeeded(player_being_challenged)
                    return ChallengeResult.challenge_succeeded, accumulated_speech

        # No  challenge happened
        return ChallengeResult.no_challenge, None

    def _counter_phase(
            self, players_without_current: list[BasePlayer], target_action: Action,
            target_player: Optional[BasePlayer] = None
    ) -> Tuple[Optional[BasePlayer], Optional[CounterAction]]:
        # Every player can choose to counter
        for countering_player in players_without_current:
            should_counter = countering_player.determine_counter(
                actor=self.current_player,
                target_player=target_player,
                action=target_action,
                state=self._build_headless_state(countering_player),
                dialogue_so_far=self._current_round_events
            )
            if should_counter:
                target_counter = get_counter_action(target_action.action_type)
                print_text(
                    build_counter_report_string(
                        target_player=self.current_player,
                        counter=target_counter,
                        countering_player=countering_player,
                    )
                )

                return countering_player, target_counter

        return None, None

    def _execute_action(
            self, action: Action, target_player: BasePlayer, countered: bool = False
    ) -> None:
        match action.action_type:
            case ActionType.income:
                # Player gets 1 coin
                self._broadcast_and_record(f"{self.current_player} takes one coin from the treasury.")
                self._take_coin_from_treasury(self.current_player, 1)
            case ActionType.foreign_aid:
                if not countered:
                    # Player gets 2 coin
                    self._broadcast_and_record(f"{self.current_player}'s takes two coins from the treasury.")
                    self._take_coin_from_treasury(self.current_player, 2)
            case ActionType.coup:
                # Player pays 7 coin
                self._broadcast_and_record(f"{self.current_player} pays 7 coins and performs the coup against {target_player}!")
                self._give_coin_to_treasury(self.current_player, 7)

                if target_player.cards:
                    # Target player loses influence
                    self._discard.append(target_player.remove_card(self._current_round_events))
            case ActionType.tax:
                # Player gets 3 coins
                self._broadcast_and_record(f"{self.current_player} takes three coins from the treasury!")
                self._take_coin_from_treasury(self.current_player, 3)
            case ActionType.assassinate:
                # Player pays 3 coin
                self._give_coin_to_treasury(self.current_player, 3)
                if not countered and target_player.cards:
                    self._broadcast_and_record(f"{self.current_player} assassinates {target_player}")
                    self._discard.append(target_player.remove_card(self._current_round_events))

            case ActionType.steal:
                if not countered:
                    # Take 2 (or all) coins from a player
                    steal_amount = min(target_player.coins, 2)
                    target_player.coins -= steal_amount
                    self.current_player.coins += steal_amount
                    self._broadcast_and_record(f"{self.current_player} steals {steal_amount} coins from {target_player}!")
            case ActionType.exchange:
                # Get 2 random cards from deck
                cards = [self._deck.pop(), self._deck.pop()]
                first_card, second_card = self.current_player.choose_exchange_cards(cards, self._current_round_events)
                self._deck.append(first_card)
                self._deck.append(second_card)
        for player in self._players:
            target_string = ""
            if target_player is not None:
                target_string = f" against {target_player}"
            if player is self.current_player:
                chat = player.determine_chat(
                    actor=self.current_player,
                    event_to_chat_about=f"You just successfully used {action.action_type}${target_string}!",
                    past_events=self._current_round_events,
                    modifier=.8
                )
            else:
                chat = player.determine_chat(
                    actor=self.current_player,
                    event_to_chat_about=f"{self.current_player} successfully performed the {action.action_type.value} action{target_string}",
                    past_events=self._current_round_events,
                    modifier=.8
            )
            if chat is not None:
                self._current_round_events.append(chat)

    def handle_turn(self) -> bool:
        # We might need to aggregate all the round dialogue into a nice array
        players_without_current = self._players_without_player(self.current_player)

        # Choose an action to perform
        target_action, target_player, speech = self._action_phase()
        if speech is not None:
            self._current_round_events.append(speech)

        # Opportunity to challenge action
        challenge_result = ChallengeResult.no_challenge
        if target_action.can_be_challenged:
            challenge_result, challenge_speech = self._challenge_phase(
                other_players=players_without_current,
                player_being_challenged=self.current_player,
                action_being_challenged=target_action,
                dialogue_so_far=[speech],
                action_target=target_player,
            )

            if challenge_speech is not None:
                for speech in challenge_speech:
                    self._current_round_events.append(speech)

        if challenge_result == ChallengeResult.challenge_succeeded:
            # Challenge succeeded and the action does not take place
            pass
        elif challenge_result == ChallengeResult.challenge_failed:
            # Challenge failed and the action is still resolved
            self._execute_action(target_action, target_player)
        elif challenge_result == ChallengeResult.no_challenge:
            # Action can't be countered
            if not target_action.can_be_countered:
                self._execute_action(target_action, target_player)

            # Opportunity to counter
            else:
                countering_player, counter = self._counter_phase(
                    players_without_current, target_action, target_player
                )

                # Opportunity to challenge counter
                counter_challenge_result = ChallengeResult.no_challenge
                if countering_player and counter:
                    players_without_countering_player = self._players_without_player(
                        countering_player
                    )
                    counter_challenge_result = self._challenge_phase(
                        other_players=players_without_countering_player,
                        player_being_challenged=countering_player,
                        action_being_challenged=counter,
                    )
                    counter_action_bluff_called = (
                            counter_challenge_result != ChallengeResult.no_challenge
                    )
                    counter_action_bluff_revealed = counter_action_bluff_called and (
                            counter_challenge_result == ChallengeResult.challenge_succeeded
                    )

                # Successfully countered and counter not challenged
                if counter and counter_challenge_result in [
                    ChallengeResult.no_challenge,
                    ChallengeResult.challenge_failed,
                ]:
                    self._execute_action(target_action, target_player, countered=True)
                # No counter occurred
                else:
                    self._execute_action(target_action, target_player)

        removed_players = []

        # Is any player out of the game?
        while player := self._remove_defeated_player():
            removed_players.append(player)
            self._broadcast_and_record(f"{player} was defeated! :skull: :skull: :skull:")
        # Have we reached a winner?
        if self._determine_win_state():
            print_text(
                f":raising_hands: Congratulations {self.remaining_player}! You are the final survivor!",
                with_markup=True,
            )
            return True

        self._next_player()
        self._last_round_events = self._current_round_events
        self._current_round_events = []

        # No winner yet
        return False
