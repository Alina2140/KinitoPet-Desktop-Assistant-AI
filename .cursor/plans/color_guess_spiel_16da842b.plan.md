---
name: Color Guess Spiel
overview: "Ein Fenster-Minispiel im Stil von What the Hex?: Hex-Code anzeigen, passende Farbkreise raten, Schwierigkeit wählen. Einbindung unter Board Games wie die anderen visuellen Spiele."
todos:
  - id: logic
    content: "color_guess.py: Rundenlogik, eindeutige Hex-Farben, apply_guess"
    status: completed
  - id: ui
    content: "color_guess_ui.py: Toplevel mit Kreisen, Gewinnzustand, Schwierigkeit"
    status: completed
  - id: wire
    content: Dialogue, game_lines, dialog_registry, GamesMixin verdrahten
    status: completed
  - id: tests
    content: Logik- und Handler-Tests ergänzen
    status: completed
isProject: false
---

# Color-Guessing-Spiel (What the Hex?)

Vorbild: [What the Hex?](https://yizzle.com/whatthehex/) — Hex-Code oben, kreisförmige Farben darunter, falsche Klicks entfernen die Farbe, richtiger Klick isoliert die Lösung.

## Spielablauf

```mermaid
flowchart TD
  start[Neue Runde] --> show["Hex-Code in Grau plus N Kreise"]
  show --> click{Klick auf Kreis}
  click -->|falsch| hide["Diesen Kreis ausblenden"]
  hide --> click
  click -->|richtig| win["Nur richtiger Kreis bleibt"]
  win --> color["Hex-Text nimmt die Zielfarbe an"]
  color --> btn["CORRECT plus NEW GAME"]
  btn --> start
  diff[Schwierigkeit ändern] --> start
```

- **Ziel:** Welche der Kreise entspricht dem angezeigten `#RRGGBB`.
- **Falsch:** nur dieser Kreis verschwindet (weiter raten).
- **Richtig:** alle anderen Kreise weg; Hex-Label in der Zielfarbe; Status `CORRECT!`; Button `NEW GAME`.
- **Schwierigkeit:** Anzahl der Optionen, wie beim Original: `2 3 4 5 6 7 8 9 10 24 48` (24 als Zwischenstufe für 48-Kreise-Layout). Standard: 9. Wechsel startet sofort eine neue Runde.

## Technik (wie Hangman / Memory)

Reines **Tkinter-Toplevel** über `open_game_window()` in [`kinito/features/games/base.py`](kinito/features/games/base.py). Menüpunkt unter **Board Games**, weil alle Fenster-Spiele dort liegen.

### Neue Dateien

- [`kinito/features/games/color_guess.py`](kinito/features/games/color_guess.py) — reine Logik (ohne Tk):
  - `DIFFICULTIES = (2, 3, 4, 5, 6, 7, 8, 9, 10, 24, 48)`
  - `random_hex()` → `#` + 6 Großbuchstaben-Hex
  - `new_round(count)` → eindeutige Hex-Liste, zufälliger `target_index`
  - `apply_guess(state, index)` → `"wrong"` / `"correct"` / `"ignored"`; falsche Indizes merken; Status `playing` | `won`
- [`kinito/features/games/color_guess_ui.py`](kinito/features/games/color_guess_ui.py) — UI analog zu [`kinito/features/games/hangman.py`](kinito/features/games/hangman.py):
  - Großes Hex-Label (neutral grau, nach Gewinn `fg=target`)
  - Canvas-Ovale als klickbare Kreise in einem wrappenden Grid (bei 48 mehrere Reihen)
  - `GUESS THE COLOR` während der Runde, `CORRECT!` + `NEW GAME` nach Gewinn
  - Schwierigkeitszeile: Zahlen als Buttons, aktuelle fett
  - Copyright-Hinweis nicht nötig (kein Klon der Marke, nur Mechanik)
  - Kinito spricht Gewinnzeilen via `speak_game_line` + `on_game_outcome("player_win")`

Fenstergröße dynamisch (klein bei 2–10, größer bei 24/48), `min_width`/`min_height` passend.

### Verdrahtung

| Datei | Änderung |
|---|---|
| [`content/dialogue.py`](content/dialogue.py) | `BUTTON_GAME_COLOR_GUESS = "Color Guess"` |
| [`content/game_lines.py`](content/game_lines.py) | kurze Win-Zeilen (und optional Fehlversuch, dezent) |
| [`content/dialog_registry.py`](content/dialog_registry.py) | Button in `BOARD_GAMES` `DialogSpec`; Mapping in `_handle_board_games` |
| [`kinito/features/games/__init__.py`](kinito/features/games/__init__.py) | Import + `start_color_guess()` wie `start_hangman()` |

Kein Highscore in [`scores.py`](kinito/features/games/scores.py) — nicht angefragt.

## Tests

- [`tests/test_games.py`](tests/test_games.py): Runde hat exakt `count` einzigartige Farben; genau ein Target; falsch blendet nur den Index aus; richtig setzt `won`; ungültiger Index / zweiter Klick nach Gewinn → `ignored`.
- [`tests/test_dialog_handlers.py`](tests/test_dialog_handlers.py): Board-Games-Button ruft `start_color_guess` auf.
