# Aegis-Tetris: Special Spins & Rotation Mechanics (SRS+) Guide

This guide documents the physics, rules, and setups for **Special Spins** in TETR.IO, detailing standard T-Spins, modern SRS+ rotation properties, and non-T piece rotations (All-Spins).

---

## 1. Standard T-Spins & Detection Rules

The T-Tetromino is the canonical piece for executing spins under standard competitive rulesets. TETR.IO detects T-Spins using the standard **3-Corner Rule**.

### The 3-Corner Rule
A rotation is classified as a T-Spin if:
1. The last successfully executed keypress prior to locking was a **rotation** (CW, CCW, or 180).
2. Out of the 4 corner cells surrounding the T-piece's center cell, at least **3 corners are filled** (occupied by placed blocks or the playfield walls/floor).

```
   [A]     [B]
      ■ ■ ■ 
      ░ ■ ░
   [C]     [D]
```
*   `[A]`, `[B]`, `[C]`, `[D]` are the four corner cells.
*   At least 3 of these must be filled.

### T-Spin Mini vs. Full T-Spin
The game distinguishes between a full T-Spin and a T-Spin Mini using the **2-Corner Rule**:
*   **Full T-Spin**: The T-piece is facing two filled corners on its *open side* (the side with 3 blocks: corners `[A]` and `[B]` when facing Up).
*   **T-Spin Mini**: The T-piece is facing only one filled corner on its open side.
*   **Kick Exemption**: Under SRS/SRS+, if the T-piece rotates using the **5th kick test** (the extreme downward kick, such as in T-Spin Triples or certain Fin T-Spins), it is elevated to a **Full T-Spin** regardless of which corners are occupied.

---

## 2. All-Spins (Custom Room Mechanics)

TETR.IO supports custom settings where all tetromino shapes (J, L, S, Z, I) can perform recognized spins. 

### Immobile Spin Detection
When `Spin Detection` is set to `All-Spins` in custom lobbies:
*   A spin is detected if a rotation is executed and the piece becomes **immobile** in its final locked state.
*   **Immobility** is defined as being unable to move the piece in any of the four cardinal directions (Up, Down, Left, or Right).
*   If the immobile piece clears lines, it triggers a **Spin Clear** (e.g., J-Spin Double, S-Spin Single, I-Spin Quad).

### Stupid-Spins
An experimental setting in TETR.IO where **any rotation that clears a line** is detected as a spin, regardless of whether the piece is blocked or immobile. 

---

## 3. Special Spin Setup Categories & Play Ideas

### A. T-Spin Double (TSD) Setups
*   **T-Overhang**: Creating a 1-cell overhang above a 3-wide pocket to leave a T-shaped notch.
*   **Imperial Guard**: An advanced TSD setup requiring a vertical tuck.
*   **T-Spin Double Cave**: Building a roof structure over the stack, keeping the entry lane open for a T-piece slide.

### B. T-Spin Triple (TST) Setups
*   Requires a 2x3 vertical pocket with a 2-cell overhang.
*   Must utilize the **SRS Kick Test 4** (rotating at the bottom of the slot shifts the piece down and under).
*   **Fin T-Spin**: A variation of the TST where the T-piece kicks into a sideways double-overhang slot.

### C. S and Z spins (The Notch Drills)
*   S and Z pieces do not slide easily under flat overhangs, but they can rotate into vertical notches.
*   **S-Triple / Z-Triple**: Uses a 3-row vertical wall with a 1-cell horizontal landing ledge. Soft-dropping the piece vertically and executing a CCW/CW rotation kicks the piece downward into the cavity.

### D. I-Spins (The Tunnel Slide)
*   In All-Spins mode, I-pieces can rotate from horizontal to vertical inside a 1-cell deep tunnel.
*   Requires specific L-shaped corners to pivot and kick the I-piece 2 blocks deep.

---

## 4. Diagnostics & AI Coaching Suggestions

We can integrate these rules into our **Aegis Spotter** and **Training Suggester**:
1.  **Missed Spin Spotting**: If the vectorizer detects a T-slot, S-notch, or Z-notch that was filled with a generic block rather than the appropriate piece, flag a **Missed Spin Opportunity** diagnostic.
2.  **Failed Spin Rewind**: If a player attempts a rotation (e.g., TST) but fails the kick angle (locking the piece out of bounds or capping the well), trigger a custom sandbox rewind to practice the rotation inputs.
3.  **B2B Chain Loss Diagnostics**: Track when a player breaks a high B2B chain. Suggest **Attack Optimization** training to teach them how to stack with spins instead of clean Singles/Doubles.
