from typing import List
from collections import deque

class TetrioRNG:
    """
    Python implementation of TETR.IO's MINSTD Lehmer Random Number Generator.
    Uses:
        a = 16807
        m = 2147483647
    This matches the reference JavaScript implementation exactly.
    """
    def __init__(self, seed: int):
        self.t = seed % 2147483647
        if self.t <= 0:
            self.t += 2147483646

    def next(self) -> int:
        """Advance the PRNG state and return the new state."""
        self.t = (16807 * self.t) % 2147483647
        return self.t

    def next_float(self) -> float:
        """Return a random float in range [0.0, 1.0)."""
        return (self.next() - 1) / 2147483646

    def shuffle_array(self, array: List) -> List:
        """
        Fisher-Yates shuffle implementation matching the Tetr.io algorithm.
        Shuffles the array in-place and returns it.
        """
        n = len(array)
        if n == 0:
            return array
            
        for i in range(n - 1, 0, -1):
            r = int(self.next_float() * (i + 1))
            array[i], array[r] = array[r], array[i]
        return array


class PieceGenerator:
    """
    Piece generator using the standard 7-bag randomizer in TETR.IO.
    Generates a continuous queue of pieces from the base pool ['Z', 'L', 'O', 'S', 'I', 'J', 'T'].
    """
    BASE_BAG = ["Z", "L", "O", "S", "I", "J", "T"]

    def __init__(self, seed: int):
        self.rng = TetrioRNG(seed)
        self.queue = deque()

    def _refill_queue(self):
        """Refills the queue with a newly shuffled 7-bag."""
        shuffled = self.rng.shuffle_array(list(self.BASE_BAG))
        self.queue.extend(shuffled)

    def next_piece(self) -> str:
        """Retrieve the next piece from the queue, generating new bags as needed."""
        if not self.queue:
            self._refill_queue()
        return self.queue.popleft()

    def peek_queue(self, length: int = 5) -> List[str]:
        """Look ahead into the queue without consuming the pieces."""
        while len(self.queue) < length:
            self._refill_queue()
        return [self.queue[i] for i in range(length)]
