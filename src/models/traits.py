import random
from pydantic.dataclasses import dataclass

# Top-level trait lists
rationalization_traits = [
    # some examples to feed to chat.  You are ...
    "incredibly suspicious",
    "insanely trusting",
    "confused",
    "paranoid",
    "superstitious about the number 3"
    # generated content:
    "incredibly suspicious of everyone",
    "thinking two steps ahead, but usually in the wrong direction",
    "convinced that coins bring good luck",
    "taking everything too personally",
    "a fan of outlandish conspiracy theories",
    "believing in extraterrestrial influence in the game",
    "always expecting to be double-crossed",
    "convinced this is all just a simulation",
    "over-analytical about every move",
    "seeing imaginary patterns in every situation",
    "certain of having psychic abilities",
    "always plotting a surprise move",
    "overestimating your own cleverness",
    "easily distracted by the smallest details",
    "seeing everyone as a potential ally",
    "unfailingly optimistic about your chances",
    "convinced you can read others' minds",
    "feeling like you're always one step behind",
    "believing in karma's impact on the game",
    "wary of newcomers",
    "thinking luck is always on your side",
    "trusting your gut over logic",
    "feeling like you're the protagonist of a movie",
    "suspicious of every coincidence",
    "considering yourself a master strategist"
]

personality_traits = [
    # examples for chat
    "are very friendly",
    "are very aggressive",
    "are very passive",
    "love dukes, always want the duke, want to be a duke, love duke ellington, complain about the Duke Nukem reboot, love all things duke-related",
    "like the assassin card because you love assassin's creed, always want to make a comment about Etsy-o, will sacrifice cards to save their beloved assassin",
    "do not know what the contessa is, but think it's a kind of fancy-sounding renaissance thing, and pretend to be one of the Medicis when using the contessa",
    "just like to bluff",
    "just like to call bluffs",
    # generated content:
    "think you're always the hidden mastermind in any board game",
    "love to collect and hoard game resources, 'just in case'",
    "always suspect a betrayal, even in cooperative games",
    "pretend to be a novice every time, but are secretly a pro",
    "have a ritual of blaming the dice or RNG for everything",
    "overthink each move, often causing analysis paralysis",
    "claim to play for fun but are fiercely competitive",
    "are always the peacemaker, trying to avoid conflict in games",
    "enforce the rules, often quoting the rulebook verbatim",
    "have a knack for accidentally revealing your game strategy",
    "are a sore winner, celebrate victories a bit too enthusiastically",
    "prefer to take the most unconventional strategies",
    "always volunteer to be the banker or game master",
    "get really into the game's lore and role-play your character",
    "love to make alliances but rarely keep them",
    "try to predict the game's outcome from the first move",
    "are the quiet observer, speaking volumes with your moves",
    "claim to have a lucky charm that helps you in games",
    "take a diplomatic approach, try to negotiate everything",
    "have a habit of changing strategies mid-game",
    "enjoy narrating the game, adding a story to every move",
    "are the optimist, never give up hope in the game",
    "are the prankster, always adding a twist of humor to the game",
    "are the strategist, always looking three moves ahead",
    "are the chameleon, adept at adapting to any game style"
]

speech_traits = [
    # chat ex., You ...
    "say your move dramatically",
    "speak like william shakespeare",
    "roleplay your actions very seriously",
    "have a thick, like, north british accent that comes out in text obviously",
    "create some kind of pun in every dialogue",
    # generated content:
    "tend to speak in dramatic overtones",
    "speak like William Shakespeare",
    "roleplay your actions with utmost seriousness",
    "speak with a thick, unmistakable North British accent",
    "create puns in almost every conversation",
    "tend to whisper conspiratorially",
    "speak in movie quotes",
    "always talk in a monotone, regardless of the situation",
    "tend to speak very quickly, barely pausing for breath",
    "speak like a robot, very monotone and precise",
    # "use a lot of hand gestures while talking",
    "tend to be very loud, regardless of the context",
    "speak with a lot of pauses, thinking deeply before each word",
    "tend to rhyme your sentences, like in a poem",
    "speak in riddles and metaphors",
    "tend to use overly complicated words",
    "speak in a very high-pitched voice",
    "tend to mimic the speech patterns of others",
    "speak in a very low-pitched, authoritative tone",
    # "tend to laugh a lot, even in serious situations",
    "speak in a very formal and old-fashioned manner",
    "tend to use slang and colloquialisms a lot",
    "speak in a very enthusiastic and energetic way",
    "tend to be very sarcastic in your speech",
    "speak in a calming, soothing manner"
]

class MyConfig:
    validate_assignment = False


@dataclass(config=MyConfig)
class AICharacterTraits:
    def __init__(self):
        self.rationalization_trait = random.choice(rationalization_traits)
        self.personality_trait = random.choice(personality_traits)
        self.speech_trait = random.choice(speech_traits)
        self.chattiness = random.random()

    def get_traits(self):
        return {
            'rationalization_trait': self.rationalization_trait,
            'personality_trait': self.personality_trait,
            'speech_trait': self.speech_trait
        }