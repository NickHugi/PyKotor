"""This module handles classes relating to editing LTR files."""
from __future__ import annotations

import random
import string

from pykotor.resource.type import ResourceType


class LTR:
    """Represents a LTR file."""

    CHARACTER_SET = string.ascii_lowercase + "'-"
    NUM_CHARACTERS = 28

    BINARY_TYPE = ResourceType.LTR

    def __init__(
        self,
    ):
        self._singles: LTRBlock = LTRBlock(LTR.NUM_CHARACTERS)
        self._doubles: list[LTRBlock] = [
            LTRBlock(LTR.NUM_CHARACTERS) for i in range(LTR.NUM_CHARACTERS)
        ]
        self._triples: list[list[LTRBlock]] = [
            [LTRBlock(LTR.NUM_CHARACTERS) for i in range(LTR.NUM_CHARACTERS)]
            for j in range(LTR.NUM_CHARACTERS)
        ]

    @staticmethod
    def _chance() -> float:
        """Returns a randomly generated float between 0.0 and 1.0 inclusive.

        Returns
        -------
            A float between 0.0 and 1.0 inclusive.
        """
        return random.uniform(0.0, 1.0)

    def generate(
        self,
        seed: int | None = None,
    ) -> str | None:
        """Returns a randomly generated name based on the LTR instance data.

        This method was ported from the C code that can be found on GitHub:
        https://github.com/mtijanic/nwn-misc/blob/master/nwnltr.c

        Args:
        ----
            seed: Randomness seed.

        Returns:
        -------
            A randomly generated name.
        """
        random.seed(seed)

        done = False

        while not done:
            attempts = 0
            name = ""

            for char in LTR.CHARACTER_SET:
                if LTR._chance() < self._singles.get_start(char):
                    name += char
                    break
            else:
                continue

            for char in LTR.CHARACTER_SET:
                index = LTR.CHARACTER_SET.index(name[-1])
                if LTR._chance() < self._doubles[index].get_start(char):
                    name += char
                    break
            else:
                continue

            for char in LTR.CHARACTER_SET:
                index1 = LTR.CHARACTER_SET.index(name[-2])
                index2 = LTR.CHARACTER_SET.index(name[-1])
                if LTR._chance() < self._triples[index1][index2].get_start(char):
                    name += char
                    break
            else:
                continue

            while True:
                prob = LTR._chance()

                if (random.randrange(0, 12) % 12) <= len(name):
                    for char in LTR.CHARACTER_SET:
                        index1 = LTR.CHARACTER_SET.index(name[-2])
                        index2 = LTR.CHARACTER_SET.index(name[-1])
                        if prob < self._triples[index1][index2].get_end(char):
                            name += char
                            return name.capitalize()

                for char in LTR.CHARACTER_SET:
                    index1 = LTR.CHARACTER_SET.index(name[-2])
                    index2 = LTR.CHARACTER_SET.index(name[-1])
                    if prob < self._triples[index1][index2].get_middle(char):
                        name += char
                        break
                else:
                    attempts += 1
                    if len(name) < 4 or attempts > 100:
                        break
        return None

    def set_singles_start(
        self,
        char: str,
        chance: float,
    ):
        self._singles.set_start(char, chance)

    def set_singles_middle(
        self,
        char: str,
        chance: float,
    ):
        self._singles.set_middle(char, chance)

    def set_singles_end(
        self,
        char: str,
        chance: float,
    ):
        self._singles.set_end(char, chance)

    def set_doubles_start(
        self,
        previous1: str,
        char: str,
        chance: float,
    ):
        self._doubles[LTR.CHARACTER_SET.index(previous1)].set_start(char, chance)

    def set_doubles_middle(
        self,
        previous1: str,
        char: str,
        chance: float,
    ):
        self._doubles[LTR.CHARACTER_SET.index(previous1)].set_middle(char, chance)

    def set_doubles_end(
        self,
        previous1: str,
        char: str,
        chance: float,
    ):
        self._doubles[LTR.CHARACTER_SET.index(previous1)].set_end(char, chance)

    def set_triples_start(
        self,
        previous2: str,
        previous1: str,
        char: str,
        chance: float,
    ):
        self._triples[LTR.CHARACTER_SET.index(previous2)][
            LTR.CHARACTER_SET.index(previous1)
        ].set_start(char, chance)

    def set_triples_middle(
        self,
        previous2: str,
        previous1: str,
        char: str,
        chance: float,
    ):
        self._triples[LTR.CHARACTER_SET.index(previous2)][
            LTR.CHARACTER_SET.index(previous1)
        ].set_middle(char, chance)

    def set_triples_end(
        self,
        previous2: str,
        previous1: str,
        char: str,
        chance: float,
    ):
        self._triples[LTR.CHARACTER_SET.index(previous2)][
            LTR.CHARACTER_SET.index(previous1)
        ].set_end(char, chance)


class LTRBlock:
    """Stores three lists where each list index is mapped to a character and the value is a float representing the chance
    of the character occuring.
    """

    def __init__(
        self,
        num_characters: int,
    ):
        self._start: list[float] = [0.0] * num_characters
        self._middle: list[float] = [0.0] * num_characters
        self._end: list[float] = [0.0] * num_characters

    def set_start(
        self,
        char: str,
        chance: float,
    ) -> None:
        """Sets the chance of a specified character at the start of the block.

        Args:
        ----
            char: The specified character from LTR.CHARACTER_SET.
            chance: The chance of occurrence from 0.0 to 1.0 inclusive.

        Raises:
        ------
            ValueError: If length of char is not 0 OR if the chance was not between 0.0 and 1.0 inclusive.
            IndexError: If char is not present in LTR.CHARACTER_SET.
        """
        if len(char) != 1:
            msg = "The character specified was not a real character."
            raise ValueError(msg)
        if char not in LTR.CHARACTER_SET:
            msg = "The character specified was invalid."
            raise IndexError(msg)
        if 0.0 > chance > 1.0:
            msg = "The chance specified must be between 0.0 and 1.0 inclusive."
            raise ValueError(msg)

        char_id = LTR.CHARACTER_SET.index(char)
        self._start[char_id] = chance

    def set_middle(
        self,
        char: str,
        chance: float,
    ) -> None:
        """Sets the chance of a specified character at the middle of the block.

        Args:
        ----
            char: char: The specified character from LTR.CHARACTER_SET.
            chance: The chance of occurrence from 0.0 to 1.0 inclusive.

        Raises:
        ------
            ValueError: If length of char is not 0 OR if the chance was not between 0.0 and 1.0 inclusive.
            IndexError: If char is not present in LTR.CHARACTER_SET.
        """
        if len(char) != 1:
            msg = "The character specified was not a real character."
            raise ValueError(msg)
        if char not in LTR.CHARACTER_SET:
            msg = "The character specified was invalid."
            raise IndexError(msg)
        if 0.0 > chance > 1.0:
            msg = "The chance specified must be between 0.0 and 1.0 inclusive."
            raise ValueError(msg)

        char_id = LTR.CHARACTER_SET.index(char)
        self._middle[char_id] = chance

    def set_end(
        self,
        char: str,
        chance: float,
    ) -> None:
        """Sets the chance of a specified character at the end of the block.

        Args:
        ----
            char: char: The specified character from LTR.CHARACTER_SET.
            chance: The chance of occurrence from 0.0 to 1.0 inclusive.

        Raises:
        ------
            ValueError: If length of char is not 0 OR if the chance was not between 0.0 and 1.0 inclusive.
            IndexError: If char is not present in LTR.CHARACTER_SET.
        """
        if len(char) != 1:
            msg = "The character specified was not a real character."
            raise ValueError(msg)
        if char not in LTR.CHARACTER_SET:
            msg = "The character specified was invalid."
            raise IndexError(msg)
        if 0.0 > chance > 1.0:
            msg = "The chance specified must be between 0.0 and 1.0 inclusive."
            raise ValueError(msg)

        char_id = LTR.CHARACTER_SET.index(char)
        self._end[char_id] = chance

    def get_start(
        self,
        char: str,
    ) -> float:
        """Returns the chance of a specified character at the start of the block.

        Args:
        ----
            char: char: The specified character from LTR.CHARACTER_SET.

        Raises:
        ------
            ValueError: If length of char is not 0.
            IndexError: If char is not present in LTR.CHARACTER_SET.

        Returns:
        -------
            The chance of a specified character at the start of the block.

        """
        if len(char) != 1:
            msg = "The character specified was not a real character."
            raise ValueError(msg)
        if char not in LTR.CHARACTER_SET:
            msg = "The character specified was invalid."
            raise IndexError(msg)

        char_id = LTR.CHARACTER_SET.index(char)
        return self._start[char_id]

    def get_middle(
        self,
        char: str,
    ) -> float:
        """Returns the chance of a specified character at the middle of the block.

        Args:
        ----
            char: char: The specified character from LTR.CHARACTER_SET.

        Raises:
        ------
            ValueError: If length of char is not 0.
            IndexError: If char is not present in LTR.CHARACTER_SET.

        Returns:
        -------
            The chance of a specified character at the start of the block.

        """
        if len(char) != 1:
            msg = "The character specified was not a real character."
            raise ValueError(msg)
        if char not in LTR.CHARACTER_SET:
            msg = "The character specified was invalid."
            raise IndexError(msg)

        char_id = LTR.CHARACTER_SET.index(char)
        return self._middle[char_id]

    def get_end(
        self,
        char: str,
    ) -> float:
        """Returns the chance of a specified character at the end of the block.

        Args:
        ----
            char: char: The specified character from LTR.CHARACTER_SET.

        Raises:
        ------
            ValueError: If length of char is not 0.
            IndexError: If char is not present in LTR.CHARACTER_SET.

        Returns:
        -------
            The chance of a specified character at the start of the block.

        """
        if len(char) != 1:
            msg = "The character specified was not a real character."
            raise ValueError(msg)
        if char not in LTR.CHARACTER_SET:
            msg = "The character specified was invalid."
            raise IndexError(msg)

        char_id = LTR.CHARACTER_SET.index(char)
        return self._end[char_id]
