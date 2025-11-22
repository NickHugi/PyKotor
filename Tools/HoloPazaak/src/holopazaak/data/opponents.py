from __future__ import annotations

from dataclasses import dataclass

from holopazaak.game.card import CardType


# All opponents from pazaak-eggborne have been ported to this file.
# Deck configurations, stand_at values, and tie_chance values match the original.
# References: vendor/pazaak-eggborne/src/scripts/characters.js


@dataclass
class OpponentProfile:
    id: str
    name: str
    description: str
    sideboard: list[tuple[int, CardType]]
    stand_at: int = 16
    tie_chance: int = 0 # Chance to accept tie (0-100)

OPPONENTS = [
    OpponentProfile(
        id="standard",
        name="Republic Soldier",
        description="A standard opponent.",
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS), (4, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS), (4, CardType.MINUS), (5, CardType.MINUS)
        ],
        stand_at=16
    ),
    OpponentProfile(
        id="jarjar",
        name="Jar Jar Binks",
        description="Meesa not be understandin' the rules too good.",
        sideboard=[
            (1, CardType.PLUS), (1, CardType.PLUS), (2, CardType.PLUS), (2, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (1, CardType.MINUS), (2, CardType.MINUS), (2, CardType.MINUS), (5, CardType.MINUS)
        ],
        stand_at=15,
        tie_chance=10
    ),
    OpponentProfile(
        id="c3po",
        name="C-3PO",
        description="Please go easy on me. I've just had my logic units calibrated.",
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS), (1, CardType.PLUS), (2, CardType.PLUS),
            (3, CardType.PLUS), (1, CardType.PLUS), (2, CardType.MINUS), (3, CardType.MINUS), (1, CardType.MINUS)
        ],
        stand_at=16,
        tie_chance=8
    ),
    OpponentProfile(
        id="porkins",
        name="Porkins",
        description="I can hold it. Give me more room to run.",
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS), (1, CardType.PLUS), (2, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS), (1, CardType.MINUS), (2, CardType.MINUS)
        ],
        stand_at=17,
        tie_chance=5
    ),
    OpponentProfile(
        id="ig88",
        name="IG-88",
        description="MISSION: DESTROY PLAYER",
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS), (4, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP)
        ],
        stand_at=20,  # Note: eggborne description says "Stands at 17" but standAt is 20
        tie_chance=3
    ),
    OpponentProfile(
        id="yoda",
        name="Yoda",
        description="Underestimated not, will I be. Beat you handily I will.",
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP)
        ],
        stand_at=18,
        tie_chance=0
    ),
    OpponentProfile(
        id="theemperor",
        name="The Emperor",
        description="In time you will call me Master.",
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP)
        ],
        stand_at=20,
        tie_chance=0
    ),
    OpponentProfile(
        id="et",
        name="E.T.",
        description="E.T. crush opponents.",
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP)
        ],
        stand_at=20,
        tie_chance=0
    ),
    OpponentProfile(
        id="thet1000",
        name="The T-1000",
        description="Say... that's a nice deck.",
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP)
        ],
        stand_at=20,
        tie_chance=0
    ),
    OpponentProfile(
        id="drchannard",
        name="Dr. Channard",
        description="And to think I hesitated.",
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP)
        ],
        stand_at=20,
        tie_chance=0
    ),
    OpponentProfile(
        id="joecamel",
        name="Joe Camel",
        description="Better be careful. I'm the geniune article.",
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP)
        ],
        stand_at=20,
        tie_chance=0
    ),
    OpponentProfile(
        id="caiaphas",
        name="Caiaphas",
        description="Fools! You have no perception! The stakes we are gambling are frightenly high!",
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP)
        ],
        stand_at=20,
        tie_chance=0
    ),
    OpponentProfile(
        id="kuato",
        name="Kuato",
        description="Start the reactor... failing that, deal up some cards!",
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP)
        ],
        stand_at=20,
        tie_chance=0
    ),
    OpponentProfile(
        id="blaine",
        name="Blaine the Monorail",
        description="I WILL TIRE QUICKLY OF BESTING YOU IN THIS SIMPLE ANCIENT GAME.",
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP)
        ],
        stand_at=20,
        tie_chance=0
    ),
    OpponentProfile(
        id="kingjaffejoffer",
        name="King Jaffe Joffer",
        description="I wouldn't trade my supreme Pazaak skills for all the riches in Zamunda.",
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP)
        ],
        stand_at=20,
        tie_chance=0
    ),
    OpponentProfile(
        id="chopchop",
        name="Chop Chop Master Onion",
        description="Stand, draw, it's all in the mind.",
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP)
        ],
        stand_at=20,
        tie_chance=0
    ),
    OpponentProfile(
        id="nu",
        name="Nu",
        description="All matches begin with Nu and end with Nu.",
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP), (4, CardType.FLIP), (5, CardType.FLIP)
        ],
        stand_at=20,
        tie_chance=0
    ),
    # Additional opponents from eggborne (using defaultStrategy with standard deck)
    OpponentProfile(
        id="bennett",
        name="Bennett from Commando",
        description="A standard opponent with basic strategy.",
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS), (4, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS), (4, CardType.MINUS), (5, CardType.MINUS)
        ],
        stand_at=16,
        tie_chance=1
    ),
    OpponentProfile(
        id="masan",
        name="Ma-san",
        description="A standard opponent with basic strategy.",
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS), (4, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS), (4, CardType.MINUS), (5, CardType.MINUS)
        ],
        stand_at=16,
        tie_chance=1
    ),
    OpponentProfile(
        id="acarrot",
        name="A Carrot",
        description="A standard opponent with basic strategy.",
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS), (4, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS), (4, CardType.MINUS), (5, CardType.MINUS)
        ],
        stand_at=16,
        tie_chance=1
    ),
    OpponentProfile(
        id="davidbowie1970s",
        name="1970s David Bowie",
        description="A standard opponent with basic strategy.",
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS), (4, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS), (4, CardType.MINUS), (5, CardType.MINUS)
        ],
        stand_at=16,
        tie_chance=1
    ),
    OpponentProfile(
        id="iliketurleskid",
        name='"I like turtles" kid',
        description="A standard opponent with basic strategy.",
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS), (4, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS), (4, CardType.MINUS), (5, CardType.MINUS)
        ],
        stand_at=16,
        tie_chance=1
    ),
    OpponentProfile(
        id="poochie",
        name="Poochie",
        description="A standard opponent with basic strategy.",
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS), (4, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS), (4, CardType.MINUS), (5, CardType.MINUS)
        ],
        stand_at=16,
        tie_chance=1
    ),
]

def get_opponent(opp_id: str) -> OpponentProfile:
    for op in OPPONENTS:
        if op.id == opp_id:
            return op
    return OPPONENTS[0]
