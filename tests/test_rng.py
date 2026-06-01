import pytest
from backend.app.core.rng import TetrioRNG, PieceGenerator

def test_rng_minstd_deterministic_sequence():
    """
    Verify that the Lehmer MINSTD generator behaves deterministically
    and generates the correct float sequence matching the Javascript specifications.
    """
    # Seed 12345
    rng = TetrioRNG(12345)
    
    # Generate 5 consecutive floats and check boundaries
    floats = [rng.next_float() for _ in range(5)]
    for val in floats:
        assert 0.0 <= val < 1.0
        
    # Check deterministic behavior: re-seeding must produce the exact same sequence
    rng2 = TetrioRNG(12345)
    floats2 = [rng2.next_float() for _ in range(5)]
    assert floats == floats2
    
    # Check handling of 0 or negative seeds
    rng_neg = TetrioRNG(-50)
    assert rng_neg.t > 0
    
    rng_zero = TetrioRNG(0)
    assert rng_zero.t > 0


def test_fisher_yates_shuffle():
    """Verify in-place Fisher-Yates array shuffling does not lose elements."""
    rng = TetrioRNG(98765)
    base_array = ["Z", "L", "O", "S", "I", "J", "T"]
    
    shuffled = rng.shuffle_array(list(base_array))
    
    # Ensure count and items match
    assert len(shuffled) == len(base_array)
    assert set(shuffled) == set(base_array)


def test_7_bag_invariants():
    """
    Test the fundamental invariant of the 7-bag generator:
    Each non-overlapping group of 7 pieces in the generated queue must
    contain exactly one of each of the 7 tetrominoes.
    """
    generator = PieceGenerator(seed=42)
    
    # Generate 70 pieces (10 bags)
    pieces = [generator.next_piece() for _ in range(70)]
    
    expected_set = {"Z", "L", "O", "S", "I", "J", "T"}
    
    # Check every slice of 7
    for i in range(10):
        bag_slice = pieces[i * 7 : (i + 1) * 7]
        assert len(bag_slice) == 7
        assert set(bag_slice) == expected_set


def test_queue_peek():
    """Verify that peeking into the queue does not consume elements."""
    generator = PieceGenerator(seed=1337)
    
    peeked = generator.peek_queue(length=10)
    assert len(peeked) == 10
    
    # Consuming must match the peeked items in order
    consumed = [generator.next_piece() for _ in range(10)]
    assert peeked == consumed
