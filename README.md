# Chess Move Explainer

A tool that suggests and explains chess moves for beginners. This application analyzes chess positions using the Stockfish engine and provides explanations that are easy to understand for players around 1000 ELO.

## Features

- Analyze chess positions from FEN strings or PGN notation
- Display the best move according to Stockfish engine
- Provide beginner-friendly explanations for why the move is good
- Show position evaluation in clear language
- Interactive board visualization in the terminal
- Option to make the suggested move and continue analysis

## Requirements

- Python 3.12 or higher
- Stockfish chess engine installed on your system

## Installation

1. Make sure you have Python 3.12+ installed
2. Install Stockfish:
   - macOS: `brew install stockfish`
   - Linux: `apt-get install stockfish` (Ubuntu/Debian) or appropriate package manager
   - Windows: Download from [Stockfish website](https://stockfishchess.org/download/) and add to PATH
3. Install the package dependencies:
   ```
   pip install -e .
   ```
   or
   ```
   pip install python-chess stockfish rich
   ```

## Usage

Run the application:

```
python hello.py
```

The program will:
1. Prompt you to enter a position in FEN or PGN format (or press Enter for the starting position)
2. Display the current board state
3. Analyze the position with Stockfish
4. Show the best move with an explanation tailored for a 1000 ELO player
5. Ask if you want to make the move and continue analysis

### Example Input Formats

**FEN (Forsyth-Edwards Notation)**:
```
rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1
```

**PGN (Portable Game Notation)**:
```
1. e4 e5 2. Nf3 Nc6
```

## Sample Explanations

The tool provides explanations like:
- "This move develops your Knight toward the center, improving your control of important squares."
- "Castling kingside puts your king in a safer position and helps connect your rooks."
- "You're winning material by capturing their Bishop."

## Limitations

- The quality of analysis depends on the installed Stockfish engine
- Some complex positional concepts may be simplified for beginner understanding
- Terminal-based board visualization has limited graphics

## Future Enhancements

- Add a graphical user interface
- Include more detailed positional explanations
- Support for saving and loading analysis
- Multi-variation analysis with alternative moves