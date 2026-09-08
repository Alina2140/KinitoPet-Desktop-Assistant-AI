"""replacement_hint_for must not treat window/casual lines as live games."""

from __future__ import annotations

from content import llm_prompts as prompts


def test_window_lines_are_not_game_reactions():
    hint = prompts.replacement_hint_for(
        "Lots of windows: Chrome, Discord. Cozy chaos. Don't leave the desk."
    )
    assert "mini-game moment" not in hint.lower()
    assert "currently playing" in hint.lower() or "invent" in hint.lower()


def test_game_invite_keeps_invitation_hint():
    hint = prompts.replacement_hint_for("How about we play a game!")
    assert hint == prompts.GAME_INVITE_HINT


def test_win_you_over_is_not_game_reaction():
    hint = prompts.replacement_hint_for(
        "That's okay. I'll win you over one day at a time. Patiently."
    )
    assert "mini-game moment" not in hint.lower()


def test_idle_and_random_prompts_forbid_invented_games():
    for text in (prompts.IDLE_PROMPT, prompts.RANDOM_QUESTION_PROMPT, prompts.SYSTEM_PROMPT):
        lower = text.lower()
        assert "currently playing" in lower or "invent that the user is currently playing" in lower


def test_app_context_forbids_invented_game_commentary():
    class _Snap:
        has_apps = True
        active = "Steam"
        open_apps = ("Steam", "Discord")

    block = prompts.app_context_block(_Snap())
    assert "playing a game" in block.lower() or "wins" in block.lower()
