"""Battleships board-game window."""

import tkinter as tk

from content import game_lines
from kinito.colors import RAINBOW_COLOR, normalize_hex_color, rainbow_at
from kinito.features.games import battleships as bs
from kinito.features.games.base import open_game_window

WATER = "#d9eff9"
PLAYER = "#7c3aed"
ENEMY = "#db6ab5"
HIT = "#bd2626"


class BattleshipsGame:
    def __init__(self, app):
        self.app = app
        self.state = bs.new_game()
        self.window = None
        self.canvas = None
        self.selected = 0
        self.vertical = False
        self.dragging = False
        self.preview = None
        self.origins = {}
        self.trays = {}
        self.cell = 24
        self._after_id = None
        self.first_hit = False
        scores = app.game_scores() if hasattr(app, "game_scores") else None
        self.best = scores.battleships_duel_best_shots() if scores else None

    def open(self):
        height = min(830, self.app.root.winfo_screenheight() - 100)
        self.window = open_game_window(self.app, "Battleships with Kinito", 560, height,
                                       min_width=520, min_height=600)
        self.app._battleships_game = self
        self.status = tk.Label(self.window, wraplength=520)
        self.status.pack(pady=6)
        self.canvas = tk.Canvas(self.window, bg="#f4eef8", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        controls = tk.Frame(self.window)
        controls.pack(pady=8)
        self.start = tk.Button(controls, text="Start battle", command=self._start)
        self.start.pack(side=tk.LEFT, padx=6)
        self.rotate = tk.Button(controls, text="Rotate (R / right-click)", command=self._rotate)
        self.rotate.pack(side=tk.LEFT, padx=6)
        tk.Button(controls, text="New Game", command=self._reset).pack(side=tk.LEFT, padx=6)
        self.canvas.bind("<Configure>", lambda event: self._draw())
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._motion)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.window.bind("<KeyPress-r>", self._rotate)
        self.window.bind("<KeyPress-R>", self._rotate)
        self.canvas.bind("<Button-3>", self._rotate)
        self.window.bind("<Destroy>", self._destroy)
        self._refresh()

    def _cancel(self):
        if self._after_id is not None:
            self.window.after_cancel(self._after_id)
            self._after_id = None

    def _destroy(self, event):
        if event.widget is self.window:
            self._cancel()
            if getattr(self.app, "_battleships_game", None) is self:
                self.app._battleships_game = None

    def _player_color(self, ship=0):
        getter = getattr(self.app, "battleships_color", None)
        color = normalize_hex_color(getter() if callable(getter) else None, PLAYER)
        return rainbow_at(ship) if color == RAINBOW_COLOR else color

    def refresh_player_colors(self):
        self._draw()

    def _reset(self):
        self._cancel()
        self.state = bs.new_game()
        self.selected = 0
        self.vertical = self.dragging = self.first_hit = False
        self.preview = None
        self._refresh()

    def _start(self):
        if bs.start_game(self.state):
            self.dragging = False
            self.preview = None
            self._refresh()

    def _index(self, x, y, side):
        ox, oy = self.origins[side]
        col, row = int((x - ox) // self.cell), int((y - oy) // self.cell)
        return row * 10 + col if 0 <= row < 10 and 0 <= col < 10 else -1

    def _press(self, event):
        self.canvas.focus_set()
        if self.state["phase"] == "playing":
            index = self._index(event.x, event.y, "kinito")
            if index >= 0:
                self._fire("player", index)
            return
        if self.state["phase"] != "placement":
            return
        index = self._index(event.x, event.y, "player")
        fleet = self.state["player"]["fleet"]
        selected = next((ship for ship, cells in fleet.items() if index in cells), None)
        if selected is None:
            selected = next((ship for ship, (x, y, w, h) in self.trays.items()
                             if x <= event.x <= x + w and y <= event.y <= y + h), None)
        if selected is not None:
            self.selected = selected
            cells = sorted(fleet.get(selected, []))
            if cells:
                self.vertical = cells[1] - cells[0] == 10
            self.dragging = True
            self._motion(event)

    def _motion(self, event):
        if self.dragging:
            self.preview = (event.x, event.y)
            self._draw()

    def _release(self, event):
        if not self.dragging:
            return
        bs.place_ship(self.state, self.selected,
                      self._index(event.x, event.y, "player"), self.vertical)
        self.dragging = False
        self.preview = None
        self._refresh()

    def _rotate(self, event=None):
        if self.state["phase"] != "placement":
            return
        self.vertical = not self.vertical
        fleet = self.state["player"]["fleet"]
        if (not self.dragging and self.selected in fleet
                and not bs.place_ship(self.state, self.selected, min(fleet[self.selected]), self.vertical)):
            self.vertical = not self.vertical
        self._draw()
        return "break"

    def _fire(self, attacker, index):
        result = bs.shoot(self.state, attacker, index)
        if result == "already":
            return
        if result == "win":
            self._end()
        elif attacker == "kinito" and result == "sunk":
            self.app.speak_game_line(game_lines.pick_game_line(
                self.app, game_lines.BATTLESHIPS_KINITO_SUNK_LINES,
            ))
        elif attacker == "player" and result in ("hit", "sunk"):
            pool = game_lines.BATTLESHIPS_HIT_LINES if self.first_hit else game_lines.BATTLESHIPS_FIRST_HIT_LINES
            self.first_hit = True
            self.app.speak_game_line(game_lines.pick_game_line(self.app, pool, "hit"))
        self._refresh()
        if self.state["phase"] == "playing" and self.state["turn"] == "kinito":
            self._after_id = self.window.after(500, self._kinito_move)

    def _kinito_move(self):
        self._after_id = None
        board = self.state["player"]
        knowledge = {key: board[key] for key in ("shots", "hits", "sunk")}
        self._fire("kinito", bs.choose_ai_shot(knowledge))

    def _end(self):
        won = self.state["winner"] == "player"
        shots = len(self.state["kinito"]["shots"])
        new_best = False
        if won:
            if hasattr(self.app, "game_scores"):
                scores = self.app.game_scores()
                new_best = scores.record_battleships_duel_shots(shots)
                self.best = scores.battleships_duel_best_shots()
            elif self.best is None or shots < self.best:
                self.best = shots
                new_best = True
        pool = (game_lines.BATTLESHIPS_NEW_BEST_LINES if new_best else game_lines.BATTLESHIPS_WIN_LINES) if won else game_lines.BATTLESHIPS_LOSE_LINES
        line = game_lines.pick_game_line(self.app, pool, "win" if won else "lose")
        self.app.speak_game_line(line.format(shots=shots, best=self.best,
                                           hits=5 - bs.ships_remaining(self.state["kinito"]), total=5))
        if hasattr(self.app, "on_game_outcome"):
            self.app.on_game_outcome("player_win" if won else "kinito_win")

    def _refresh(self):
        phase = self.state["phase"]
        if phase == "placement":
            count = len(self.state["player"]["fleet"])
            text = f"Place your fleet ({count}/5). Drag ships onto your board; R / right-click to rotate."
        elif phase == "finished":
            text = "You win!" if self.state["winner"] == "player" else "Kinito wins! Your fleet was sunk."
        else:
            text = "Your turn — click Kinito's board." if self.state["turn"] == "player" else "Kinito is aiming…"
            text += " Hits give another shot."
        if phase != "placement":
            text += (f" Ships left: you {bs.ships_remaining(self.state['player'])},"
                     f" Kinito {bs.ships_remaining(self.state['kinito'])}."
                     f" Your shots: {len(self.state['kinito']['shots'])}.")
        if self.best is not None:
            text += f" Best win: {self.best} shots."
        self.status.config(text=text)
        self.start.config(state="normal" if phase == "placement" and len(self.state["player"]["fleet"]) == 5 else "disabled")
        self.rotate.config(state="normal" if phase == "placement" else "disabled")
        self._draw()

    def _draw(self):
        c = self.canvas
        if c is None:
            return
        c.delete("all")
        width, height = max(c.winfo_width(), 500), max(c.winfo_height(), 440)
        self.cell = max(12, min((width - 215) / 10, (height - 100) / 20))
        size = self.cell * 10
        x = max(35, (width - size - 175) / 2)
        self.origins = {"kinito": (x, 35), "player": (x, size + 85)}
        for side, (ox, oy) in self.origins.items():
            board = self.state[side]
            c.create_text(ox + size / 2, oy - 30, text="Kinito's waters" if side == "kinito" else "Your fleet", font=("Segoe UI", 11, "bold"))
            for n in range(10):
                c.create_text(ox + (n + .5) * self.cell, oy - 12, text=chr(65 + n))
                c.create_text(ox - 15, oy + (n + .5) * self.cell, text=str(n + 1))
            for index in range(100):
                row, col = divmod(index, 10)
                left, top = ox + col * self.cell, oy + row * self.cell
                visible = side == "player" or self.state["phase"] == "finished"
                ship = next((key for key, cells in board["fleet"].items() if index in cells), None)
                fill = (self._player_color(ship) if side == "player" else ENEMY) if visible and ship is not None else WATER
                if index in board["sunk"]:
                    fill = "#694747"
                c.create_rectangle(left, top, left + self.cell, top + self.cell, fill=fill, outline="#829bad")
                if index in board["hits"]:
                    pad = self.cell * .22
                    c.create_line(left + pad, top + pad, left + self.cell - pad, top + self.cell - pad, fill=HIT, width=3)
                    c.create_line(left + pad, top + self.cell - pad, left + self.cell - pad, top + pad, fill=HIT, width=3)
                elif index in board["shots"]:
                    pad = self.cell * .38
                    c.create_oval(left + pad, top + pad, left + self.cell - pad, top + self.cell - pad, fill="#234960", outline="")
        tx, ty = x + size + 20, self.origins["player"][1]
        c.create_text(tx, ty, text="Your ships", anchor="nw", font=("Segoe UI", 11, "bold"))
        self.trays = {}
        for ship, length in enumerate(bs.SHIP_LENGTHS):
            y = ty + 30 + ship * 38
            placed = ship in self.state["player"]["fleet"]
            c.create_text(tx, y, text=f"{length} cells" + (" — placed" if placed else ""), anchor="nw")
            if not placed:
                self.trays[ship] = (tx, y + 17, length * 20, 16)
                for part in range(length):
                    c.create_rectangle(tx + part * 20, y + 17, tx + (part + 1) * 20, y + 33,
                                       fill=self._player_color(ship), outline="white", width=2 if self.selected == ship else 1)
        c.create_text(tx, 35, text="× Hit   • Miss\nDark = sunk\n\nShips may touch.\nDrag, then release.\nR = rotate 90°", anchor="nw", width=135)
        if self.dragging and self.preview:
            px, py = self.preview
            index = self._index(px, py, "player")
            cells = bs.ship_cells(self.selected, index, self.vertical)
            valid = bs.can_place(self.state["player"]["fleet"], self.selected, cells)
            if index >= 0:
                row, col = divmod(index, 10)
                px = x + col * self.cell
                py = self.origins["player"][1] + row * self.cell
            for part in range(bs.SHIP_LENGTHS[self.selected]):
                left = px + (0 if self.vertical else part * self.cell)
                top = py + (part * self.cell if self.vertical else 0)
                c.create_rectangle(left, top, left + self.cell, top + self.cell,
                                   outline="#168243" if valid else "#df2929", width=3)
