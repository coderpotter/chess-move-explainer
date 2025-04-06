#!/usr/bin/env python3
import chess
import chess.pgn
import chess.engine
import os
import sys
import io
import platform
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def get_stockfish_path():
    """Attempt to find the Stockfish executable with improved detection."""
    # Common paths where Stockfish might be installed
    system = platform.system()
    
    if system == "Darwin":  # macOS
        possible_paths = [
            "stockfish",
            "/usr/local/bin/stockfish",
            "/opt/homebrew/bin/stockfish",  # For Apple Silicon Macs
            str(Path.home() / "bin" / "stockfish"),
            str(Path.home() / "Downloads" / "stockfish")
        ]
    elif system == "Linux":
        possible_paths = [
            "stockfish",
            "/usr/bin/stockfish",
            "/usr/local/bin/stockfish",
            str(Path.home() / "bin" / "stockfish")
        ]
    elif system == "Windows":
        possible_paths = [
            "stockfish.exe",
            str(Path("C:\\") / "Program Files" / "Stockfish" / "stockfish.exe"),
            str(Path.home() / "Downloads" / "stockfish" / "stockfish.exe")
        ]
    else:
        possible_paths = ["stockfish"]
    
    # First check if stockfish is available in PATH
    try:
        # Use 'where' on Windows, 'which' on Unix-like systems
        which_cmd = "where" if system == "Windows" else "which"
        result = subprocess.run([which_cmd, "stockfish"], 
                                capture_output=True, 
                                text=True,
                                check=False)
        if result.returncode == 0 and result.stdout.strip():
            stockfish_path = result.stdout.strip().split('\n')[0]
            console.print(f"[green]Found Stockfish at: {stockfish_path}[/]")
            return stockfish_path
    except Exception:
        pass
    
    # Try the predefined paths
    for path in possible_paths:
        try:
            # Check if the file exists
            if system == "Windows" and not path.endswith(".exe"):
                check_path = path + ".exe"
            else:
                check_path = path
                
            if os.path.isfile(check_path) and os.access(check_path, os.X_OK):
                console.print(f"[green]Found Stockfish at: {check_path}[/]")
                return check_path
                
            # Try running with a longer timeout since 0.1s might be too short
            engine = chess.engine.SimpleEngine.popen_uci(path, timeout=2.0)
            engine.quit()
            console.print(f"[green]Found Stockfish at: {path}[/]")
            return path
        except (chess.engine.EngineTerminatedError, FileNotFoundError, OSError):
            continue
    
    console.print("[bold red]Error: Stockfish engine not found![/]")
    console.print("Please install Stockfish and make sure it's in your PATH.")
    console.print("Installation instructions:")
    console.print("- macOS: brew install stockfish")
    console.print("- Linux: apt-get install stockfish (Ubuntu/Debian)")
    console.print("- Windows: Download from https://stockfishchess.org/download/")
    console.print("\nAfter installing, restart this application.")
    sys.exit(1)

def parse_position(position_str):
    """Parse a position string (FEN or PGN) and return a chess.Board."""
    # Check if the input is a FEN string
    try:
        board = chess.Board(position_str)
        return board
    except ValueError:
        pass
    
    # Check if the input is a PGN string
    try:
        pgn = chess.pgn.read_game(io.StringIO(position_str))
        if pgn is not None:
            board = pgn.end().board()
            return board
    except Exception:
        pass
        
    # If we reached here, the input is invalid
    return None

def explain_move(move, board, is_white_to_move):
    """Generate a beginner-friendly explanation for a chess move."""
    piece = board.piece_at(move.from_square)
    piece_name = chess.piece_name(piece.piece_type).capitalize()
    from_square = chess.square_name(move.from_square)
    to_square = chess.square_name(move.to_square)
    
    explanations = []
    
    # Basic move description
    move_text = f"{piece_name} from {from_square} to {to_square}"
    
    # Check if it's a capture
    capture_piece = board.piece_at(move.to_square)
    if capture_piece:
        captured = chess.piece_name(capture_piece.piece_type).capitalize()
        move_text += f", capturing a {captured}"
        explanations.append(f"You're winning material by capturing their {captured}.")
    
    # Check if it's a check
    test_board = board.copy()
    test_board.push(move)
    if test_board.is_check():
        move_text += ", giving check"
        explanations.append("This move puts the opponent's king in check.")
    
    # Check if it's a promotion
    if move.promotion:
        promoted_piece = chess.piece_name(move.promotion).capitalize()
        move_text += f", promoting to {promoted_piece}"
        explanations.append(f"Your pawn promotes to a {promoted_piece}, gaining a powerful piece.")
    
    # Piece development explanation for early game
    if board.fullmove_number < 10:
        central_squares = [chess.parse_square(s) for s in ['d4', 'e4', 'd5', 'e5']]
        if move.to_square in central_squares and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            explanations.append(f"This move develops your {piece_name} toward the center, improving your control of important squares.")
    
    # Pawn structure explanations
    if piece.piece_type == chess.PAWN:
        explanations.append("Advancing a pawn helps control more territory on the board.")
    
    # King safety
    if piece.piece_type == chess.KING and board.fullmove_number < 15:
        if move.from_square == chess.E1 and move.to_square == chess.G1:  # White kingside castle
            explanations.append("Castling kingside puts your king in a safer position and helps connect your rooks.")
        elif move.from_square == chess.E1 and move.to_square == chess.C1:  # White queenside castle
            explanations.append("Castling queenside puts your king in a safer position and helps connect your rooks.")
        elif move.from_square == chess.E8 and move.to_square == chess.G8:  # Black kingside castle
            explanations.append("Castling kingside puts your king in a safer position and helps connect your rooks.")
        elif move.from_square == chess.E8 and move.to_square == chess.C8:  # Black queenside castle
            explanations.append("Castling queenside puts your king in a safer position and helps connect your rooks.")
    
    # If we couldn't generate specific explanations, use a generic one
    if not explanations:
        side = "white" if is_white_to_move else "black"
        explanations.append(f"This is the best move for {side} in this position according to computer analysis.")
    
    return move_text, explanations

def generate_ai_explanation(board, best_move, next_moves, score, is_white_to_move):
    """Generate a detailed AI-powered explanation for the best move."""
    # Extract information about the position
    piece = board.piece_at(best_move.from_square)
    piece_name = chess.piece_name(piece.piece_type).capitalize()
    from_square = chess.square_name(best_move.from_square)
    to_square = chess.square_name(best_move.to_square)
    
    # Check if the move is a capture
    capture_piece = board.piece_at(best_move.to_square)
    is_capture = capture_piece is not None
    
    # Check if it's a check
    test_board = board.copy()
    test_board.push(best_move)
    is_check = test_board.is_check()
    
    # Check if it's a promotion
    is_promotion = best_move.promotion is not None
    
    # Get the side to move
    side = "White" if is_white_to_move else "Black"
    
    # Generate the explanation based on the context
    explanation = []
    
    # Basic move description
    move_description = f"The best move is {piece_name} from {from_square} to {to_square}"
    if is_capture:
        captured = chess.piece_name(capture_piece.piece_type).capitalize()
        move_description += f", capturing a {captured}"
    if is_check:
        move_description += ", giving check"
    if is_promotion:
        promoted_piece = chess.piece_name(best_move.promotion).capitalize()
        move_description += f", promoting to {promoted_piece}"
    
    explanation.append(move_description + ".")

    # Strategic explanation based on the position
    if len(next_moves) > 0:
        # Create a brief explanation of the next few moves
        future_line = []
        future_board = board.copy()
        future_board.push(best_move)  # Start with the best move already made
        
        for i, move in enumerate(next_moves):
            try:
                # Get the proper SAN notation which correctly includes 'x' for captures
                san_move = future_board.san(move)
                future_board.push(move)
                mover = "Your opponent" if i % 2 == 0 else "You"
                future_line.append(f"{mover} play {san_move}")
            except Exception:
                break
        
        if future_line:
            line_explanation = " then ".join(future_line[:3]) + "."
            explanation.append(f"Looking ahead, {line_explanation}")

    # Determine game phase based on material count and move number
    # Count material to better determine game phase
    white_pieces = len([p for p in board.piece_map().values() if p.color])
    black_pieces = len([p for p in board.piece_map().values() if not p.color])
    total_pieces = white_pieces + black_pieces
    
    # More accurate game phase detection
    if total_pieces >= 26 or board.fullmove_number <= 10:
        phase = "opening"
    elif total_pieces >= 14:
        phase = "middlegame"
    else:
        phase = "endgame"
        
    # Override for very late moves
    if board.fullmove_number >= 40:
        phase = "endgame"
    
    # Opening-specific advice
    if phase == "opening":
        if piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            explanation.append(f"This move develops your {piece_name}, which is important in the opening. Aim to control the center and develop all your pieces before launching an attack.")
        elif piece.piece_type == chess.PAWN and (from_square[0] == 'd' or from_square[0] == 'e'):
            explanation.append("Controlling the center with your pawns gives you more space and options for your pieces.")
        elif best_move.from_square == chess.E1 and best_move.to_square == chess.G1:  
            explanation.append("Castling keeps your king safe and connects your rooks. This is a key opening goal.")
        elif best_move.from_square == chess.E8 and best_move.to_square == chess.G8:
            explanation.append("Castling keeps your king safe and connects your rooks. This is a key opening goal.")
    
    # Middlegame specific advice
    elif phase == "middlegame":
        if is_capture:
            captured = chess.piece_name(capture_piece.piece_type).capitalize()
            explanation.append(f"Taking their {captured} gives you a material advantage, which can be converted to a win with careful play.")
        elif is_check:
            explanation.append("Checking the king forces your opponent to respond to the threat, which gives you initiative to execute your plan.")
        elif piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            explanation.append(f"Repositioning your {piece_name} to a more active square improves your piece coordination and creates new threats.")
    
    # Endgame specific advice
    else:
        if piece.piece_type == chess.PAWN:
            explanation.append("In the endgame, advancing pawns toward promotion is often decisive. Each pawn that promotes gains you a queen!")
        elif piece.piece_type == chess.KING:
            explanation.append("In the endgame, the king becomes a powerful piece. Don't be afraid to use it actively.")
        elif is_capture:
            captured = chess.piece_name(capture_piece.piece_type).capitalize()
            explanation.append(f"In the endgame, trading pieces when ahead (or avoiding trades when behind) is a key principle. This capture of their {captured} is following that strategy.")
        else:
            explanation.append("In the endgame, piece activity and coordination are crucial. This move improves your piece position.")
    
    # Add tactical explanation based on evaluation
    if score is not None:
        score_in_pawns = abs(score) / 100
        if score_in_pawns > 3:
            if (score > 0 and is_white_to_move) or (score < 0 and not is_white_to_move):
                explanation.append("You have a winning advantage. Focus on simplifying the position while maintaining your advantage.")
            else:
                explanation.append("Your position is challenging, but this move gives you the best fighting chance.")
        elif score_in_pawns > 1:
            if (score > 0 and is_white_to_move) or (score < 0 and not is_white_to_move):
                explanation.append("You have a clear advantage. Look for tactical opportunities while avoiding piece trades when you're ahead.")
            else:
                explanation.append("You're at a disadvantage, but this move helps minimize your opponent's edge. Look for counterplay.")
    
    return explanation

def analyze_position(board, depth=15, num_variations=1):
    """Analyze a chess position and return the best move with explanation."""
    try:
        stockfish_path = get_stockfish_path()
        
        # Initialize the engine with a longer timeout
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, timeout=10.0)
        
        try:
            # Set a higher skill level for better analysis
            engine.configure({"Skill Level": 20})
        except Exception:
            # Not all versions of Stockfish support this option
            console.print("[yellow]Note: Could not configure skill level. Using default.[/]")
        
        # Get the analysis with a reasonable time limit
        console.print("[bold]Running analysis (this may take a few seconds)...[/]")
        info = engine.analyse(
            board, 
            chess.engine.Limit(depth=depth, time=5.0),  # Add time limit as backup
            multipv=num_variations
        )
        
        # Close the engine
        engine.quit()
        
        # Extract the best move and future moves
        best_move = info[0]["pv"][0]
        next_moves = info[0]["pv"][1:6] if len(info[0]["pv"]) > 1 else []
        score = info[0]["score"].relative.score(mate_score=10000)
        
        # Generate basic move info
        move_text, basic_explanations = explain_move(best_move, board, board.turn)
        
        # Generate enhanced AI explanation
        ai_explanations = generate_ai_explanation(board, best_move, next_moves, score, board.turn)
        
        # Format the score
        if score is not None:
            if score > 0:
                advantage = "White is ahead" if board.turn else "You can reduce Black's advantage"
            else:
                advantage = "Black is ahead" if not board.turn else "You can reduce White's advantage"
            
            # Convert centipawns to pawns
            score_in_pawns = abs(score) / 100
            if score_in_pawns >= 10:
                evaluation = "completely winning"
            elif score_in_pawns >= 5:
                evaluation = "clearly winning"
            elif score_in_pawns >= 3:
                evaluation = "significantly better"
            elif score_in_pawns >= 1.5:
                evaluation = "better"
            elif score_in_pawns >= 0.5:
                evaluation = "slightly better"
            else:
                evaluation = "roughly equal"
            
            advantage = f"{advantage} (position is {evaluation})"
        else:
            # Handle mate scores
            mate_score = info[0]["score"].relative.mate()
            if mate_score is not None:
                if mate_score > 0:
                    advantage = f"{'White' if board.turn else 'Black'} can force mate in {mate_score} moves"
                else:
                    advantage = f"{'White' if board.turn else 'Black'} is getting mated in {abs(mate_score)} moves"
            else:
                advantage = "Position is unclear"
        
        return best_move, advantage, move_text, ai_explanations
    
    except Exception as e:
        console.print(f"[bold red]Error during analysis: {e}[/]")
        console.print("[bold yellow]Try installing Stockfish using: brew install stockfish (on macOS)[/]")
        return None, None, None, None

def print_board(board):
    """Print the chess board with nice formatting."""
    console.print("\n[bold]Current Board Position:[/]")
    
    # Create a visual representation of the board
    board_str = str(board)
    
    # Replace piece symbols with more readable ones if needed
    # board_str = board_str.replace("r", "♜").replace("n", "♞")...
    
    console.print(Panel(board_str, expand=False))
    
    # Print whose turn it is
    turn = "White" if board.turn else "Black"
    console.print(f"[bold]{turn} to move[/]")
    
    # Print FEN for reference
    console.print(f"FEN: {board.fen()}\n")

def main():
    console.print("[bold blue]♞ Chess Move Explainer[/]")
    console.print("A tool that suggests and explains chess moves for beginners\n")
    
    while True:
        console.print("[bold green]Enter a position (FEN or PGN), 'q' to quit, or press Enter for the starting position:[/]")
        position_input = input().strip()
        
        if position_input.lower() in ['q', 'quit', 'exit']:
            break
        
        # Use the starting position if no input is provided
        if not position_input:
            board = chess.Board()
        else:
            board = parse_position(position_input)
            if board is None:
                console.print("[bold red]Invalid position format. Please enter a valid FEN or PGN.[/]")
                continue
        
        # Display the board
        print_board(board)
        
        # Analyze the position
        console.print("[bold]Analyzing position...[/]")
        best_move, advantage, move_text, explanations = analyze_position(board)
        
        if best_move is None:
            continue
        
        # Display the results
        console.print(f"\n[bold green]Best Move:[/] {board.san(best_move)} ({move_text})")
        console.print(f"[bold]Evaluation:[/] {advantage}")
        
        console.print("\n[bold]Enhanced Explanation for a 1000 ELO player:[/]")
        for i, explanation in enumerate(explanations, 1):
            console.print(f"{i}. {explanation}")
        
        # Ask if the user wants to make the move and continue analysis
        console.print("\n[bold green]Would you like to make this move and continue analysis? (y/n)[/]")
        continue_input = input().strip().lower()
        
        if continue_input in ['y', 'yes']:
            board.push(best_move)
            print_board(board)
        
        console.print("\n" + "-" * 50 + "\n")

if __name__ == "__main__":
    main()
