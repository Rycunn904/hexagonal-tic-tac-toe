class HexTTT:
    def __init__(self):
        self.board = {}
        self.current_player = 1
        self.round_number = 1
        self.pieces_to_place = 1
        self.current_radius = 10
        self.winner = None
        self.ensure_radius()
    
    def ensure_radius(self):
        # Ensure the board has all positions within the current radius
        for q in range(-self.current_radius, self.current_radius + 1):
            for r in range(-self.current_radius, self.current_radius + 1):
                s = -q - r
                if abs(s) <= self.current_radius:
                    if (q, r, s) not in self.board:
                        self.board[(q, r, s)] = 0
    
    def check_win(self):
        # 6 in a row is a win on a hex grid
        directions = [(1, 0, -1), (0, 1, -1), (1, -1, 0)]
        for (q, r, s), value in self.board.items():
            if value != self.current_player:
                continue
            for dq, dr, ds in directions:
                count = 1
                # forward direction
                for i in range(1, 6):
                    nq, nr, ns = q + i * dq, r + i * dr, s + i * ds
                    if self.board.get((nq, nr, ns)) == self.current_player:
                        count += 1
                    else:
                        break
                # backward direction
                for i in range(1, 6):
                    nq, nr, ns = q - i * dq, r - i * dr, s - i * ds
                    if self.board.get((nq, nr, ns)) == self.current_player:
                        count += 1
                    else:
                        break
                if count >= 6:
                    self.winner = self.current_player
                    return True
        return False
    
    def place_piece(self, q, r, s):
        if (q, r, s) in self.board and self.board[(q, r, s)] == 0:
            self.board[(q, r, s)] = self.current_player
            return True
        return False
    
    def next_turn(self):
        # first round, only 1 piece for starter player, then 2 pieces for each player in subsequent rounds
        if self.pieces_to_place > 1:
            self.pieces_to_place -= 1
        else:
            self.current_player = 2 if self.current_player == 1 else 1
            self.round_number += 1
            self.pieces_to_place = 2

    def expand_board(self):
        self.current_radius += 1
        self.ensure_radius()
        

    def get_game_state(self):
        # Convert tuple keys to string for JSON serialization
        serialized_board = {f"{q},{r},{s}": owner for (q, r, s), owner in self.board.items()}
        return {
            'board': serialized_board,
            'current_player': self.current_player,
            'round_number': self.round_number,
            'winner': self.winner,
            'current_radius': self.current_radius,
            'pieces_to_place': self.pieces_to_place
        }