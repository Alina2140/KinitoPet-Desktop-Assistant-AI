---
name: More Fixed Lines
overview: Kleine Line-Pools (~unter 25 Einträge) ungefähr verdoppeln; große Pools (dialogue-Fragen, facts, poems, quotes, mood, memory) jeweils um ~10–15 erweitern. Neue Texte ohne „soft/softly“; bestehende Soft-Wiederholungen in mood_lines.py und facts.py umschreiben.
todos:
  - id: soft-cleanup
    content: "mood_lines.py + facts.py: Soft-Wiederholungen umschreiben"
    status: completed
  - id: small-lines
    content: Kleine *_lines.py, paint, music, hug, game_lines, startup verdoppeln bzw. +10–15
    status: completed
  - id: dialogue
    content: "dialogue.py: Fragen/Responses/Feature-Pools erweitern (Marker behalten)"
    status: completed
  - id: literary
    content: poems (+10–15), stories verdoppeln, quotes (+10–15), wisdom intros, facts (+10–15)
    status: completed
  - id: extra-pools
    content: special_days, magic_8_ball, trivia, hangman, memory_followups ergänzen
    status: completed
  - id: qa
    content: Import-Check + Grep gegen soft/softly (außer TTS-Marker)
    status: completed
isProject: false
---

# Mehr feste Lines + Soft-Cleanup

## Entscheidungen
- **Menge:** Listen mit **&lt; ~25** Einträgen ungefähr **verdoppeln**; große Pools **+10–15** neue Einträge.
- **Soft:** In **neuen** Lines kein `soft`/`softly`/ähnliche Varianten. Zusätzlich Hotspots **[`content/mood_lines.py`](content/mood_lines.py)** und **[`content/facts.py`](content/facts.py)** umschreiben (bestehende Soft-Stotter-Zeilen). TTS-Marker in dialogue (z. B. „soft, normal, or loud“) **unberührt**.

## Stil (für alle neuen Texte)
- Englisch, Kinito-Ton: niedlich/creepy/clingy, Desktop-Freundschaft, Creepiness wo passend.
- Bestehende Platzhalter/Marker exakt beibehalten (`{song}`, `{active_app}`, Yes/No-Marker-Substrings, Poem-Dict-Felder `text`/`whisper`/`play_music`/`themes`, Quote-Schema `quote`/`author`/`source`).
- Keine Duplikate zu bestehenden Lines; keine Code-Logik ändern, nur Content-Listen.

## Scope nach Datei-Gruppe

### A) Kleine `*_lines.py` — verdoppeln
Je Liste von ~n auf ~2n (bei schon ~20–24 eher +15–20, nicht mechanisch aufblasen):

- [`ads_lines.py`](content/ads_lines.py), [`dizzy_lines.py`](content/dizzy_lines.py), [`goodbye_lines.py`](content/goodbye_lines.py), [`head_stroke_lines.py`](content/head_stroke_lines.py), [`hold_lines.py`](content/hold_lines.py), [`hug_lines.py`](content/hug_lines.py) (`HUG_LINES` + `HUG_ASK_LINES`), [`throw_lines.py`](content/throw_lines.py), [`window_grab_lines.py`](content/window_grab_lines.py)
- [`browser_lines.py`](content/browser_lines.py) (`BROWSER_LINES` + `HORROR_BROWSER_LINES`)
- [`music_player_lines.py`](content/music_player_lines.py): alle 4 Listen; Pause-Nudges **müssen** Substring `want to keep listening` enthalten
- [`paint_lines.py`](content/paint_lines.py): alle kleinen Pools (~7–11) verdoppeln
- [`app_lines.py`](content/app_lines.py): `APP_AWARE_*` (~28–30) → +10–15 (Grenze „groß“)
- [`camera_lines.py`](content/camera_lines.py), [`fancy_lines.py`](content/fancy_lines.py), [`screen_comment_lines.py`](content/screen_comment_lines.py), [`startup.py`](content/startup.py): schon ~40+ → **+10–15**
- [`nudge_lines.py`](content/nudge_lines.py): drei Listen (~26–36) → je **+10–15**
- [`game_lines.py`](content/game_lines.py): jede Reaction-Liste (~4–7) verdoppeln; Platzhalter beibehalten

### B) [`dialogue.py`](content/dialogue.py) — selektiv erweitern
- Jede `*_QUESTIONS`-Liste und kleine Response-/Ack-/Feature-UI-Liste (&lt;~25): ungefähr verdoppeln; Marker-Substring der kanonischen Frage in jeder Variante behalten.
- Schon große Pools (z. B. Jokes ~36, Compliments ~22): **+10–15** bzw. verdoppeln wenn noch unter 25.
- Keine Änderungen an Helper-Funktionen (`pick_line`, …) oder Marker-Konstanten.

### C) Mood Soft-Cleanup + Erweiterung — [`mood_lines.py`](content/mood_lines.py)
1. Alle Einträge mit wiederholtem/überflüssigem `soft`/`softly` umschreiben (gleicher Sinn, andere Wörter: quiet, gentle, calm, muted, tender, … sparsam und abwechslungsreich).
2. Pro Mood-Unterliste je nach Größe verdoppeln oder +10–15 (`IDLE_SNIPPETS_BY_MOOD` ist groß → pro Mood +~5–8, insgesamt im +10–15-Geist pro Mood-Bucket).

### D) Poems / Stories / Facts / Quotes / Wisdom
- [`poems.py`](content/poems.py): **+10–15** neue Dicts (Mix whisper/music; optional `themes` für Saison); kein Soft-Füllwort.
- [`stories.py`](content/stories.py): **verdoppeln** (~21 → ~40–42 Kurzgeschichten).
- [`facts.py`](content/facts.py): Soft-Zeilen umschreiben **und** **+10–15** neue dunkle/freundschaftliche Trivia.
- [`quotes.json`](content/quotes.json): **+10–15** echte/anonyme Zitate (Schema beibehalten); [`wisdom.py`](content/wisdom.py) `_INTROS` verdoppeln (~42 → ~80-ish, oder +10–15 wenn als „groß“ gewertet — hier: **+10–15 Intros**, Quotes kommen aus JSON).

### E) Weitere feste Pools (mit im Scope „alles“)
- [`special_days.py`](content/special_days.py): pro Occasion wo Lines dünn sind, ergänzen (Gesamtziel eher +10–15 Lines bzw. verdoppeln wo Listen &lt;25).
- [`magic_8_ball.py`](content/magic_8_ball.py): Antworten verdoppeln (~20 → ~40).
- [`trivia_questions.py`](content/trivia_questions.py): je Pack **+10–15** True/False (nicht verdoppeln der 140).
- [`hangman_words.py`](content/hangman_words.py): **+10–15** Wörter (Pool schon groß).
- [`memory_followups.py`](content/memory_followups.py): `MEMORY_FOLLOWUPS` Topics/Templates um **+10–15** Templates insgesamt sinnvoll verteilen; `FACT_UPDATE_PROMPTS` nicht massiv verdoppeln (schon riesig) — nur wo Keys auffällig dünn sind, +wenige Varianten.

### F) Explizit auslassen
- `llm_prompts.py`, Registry/Validatoren, `questions.py` (Aggregator), `birthday.py`/`friendship.py` (Logik ohne Line-Pools), `credits.py`.

## Arbeitsreihenfolge
1. Soft-Cleanup `mood_lines.py` + `facts.py`
2. Alle kleinen `*_lines.py` + `game_lines` + `startup`
3. `dialogue.py` Fragen/Responses/Feature-Lines
4. Poems, Stories, Quotes (+ Wisdom-Intros), Facts-Erweiterung
5. special_days, magic_8_ball, trivia, hangman, memory_followups (dünne Stellen)
6. Kurzer Grep-Check: neues `soft`/`softly` in geänderten Content-Dateien (außer TTS-Marker); Syntax-Check der `.py`-Module

## Qualitätssicherung
- Nach Batch: `python -c "import content.…"` für geänderte Module bzw. gezielter Import der Content-Pakete.
- Grep auf `\bsoft` in `mood_lines`/`facts` und neuen Diffs; erlaubte Ausnahme nur bekannte Marker in `dialogue.py`.
