# Poker-tracker

### Description:

This repository contains code for visualizing online Poker session results (see a sample
in `/plots`). The information gets extracted from raw poker hand history files which are
provided as `.txt` files by most Poker websites. The code is suitable for 888 Poker and
Pokerstars cash game hand histories.

Multiple hand history files, e.g. from multiple tables played simultaneously, can be
processed by the Poker tracker. The hands played will be sorted by date to reflect the
actual evolution of winnings or losings over time.

### Instructions:

1. Paste the hand history files in `/hand_histories`. They should follow the naming pattern
   of the existing file pattern in order to automatically detect the website name.
2. In `main.py`, specify `hero` (account name) and `file_names`.
3. Run `main.py`.
   
The chart will then be available in `/plots`.

### Limitations:

The program may not yet yield perfect results for very rare cases like multi-way main
pot / side pot constellations.
