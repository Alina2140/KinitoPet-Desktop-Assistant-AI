"""Paths to sprites, sounds, and the optional TTS engine (balcon / pyttsx3)."""

import math
import os

try:
    import pyttsx3

    engine = pyttsx3.init()
except Exception:
    engine = None

script_directory = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
assets_directory = os.path.join(script_directory, "GameAssets")
sprites_directory = os.path.join(assets_directory, "sprites")
sprites_standing_directory = os.path.join(sprites_directory, "Standing")
sprites_standing2_directory = os.path.join(sprites_directory, "Standing2")
sprites_reading_directory = os.path.join(sprites_directory, "Reading")
sprites_magic_directory = os.path.join(sprites_directory, "Magic")
sprites_surfing_directory = os.path.join(sprites_directory, "Surfing")
sprites_sleeping_directory = os.path.join(sprites_directory, "Sleeping")
sprites_talking_directory = os.path.join(sprites_directory, "Talking")
sprites_thinking_directory = os.path.join(sprites_directory, "Thinking")
sprites_hugging_directory = os.path.join(sprites_directory, "Hugging")
icons_directory = os.path.join(assets_directory, "icons")
sounds_directory = os.path.join(assets_directory, "sounds")
secret_images_directory = os.path.join(assets_directory, "SecretImages")
programs_directory = os.path.join(assets_directory, "Programs")
ads_directory = os.path.join(assets_directory, "ads")
websites_directory = os.path.join(assets_directory, "websites")
user_media_directory = os.path.join(assets_directory, "UserMedia")
crash_directory = os.path.join(assets_directory, "crash")
balconexe_directory = os.path.join(programs_directory, "balcon.exe")

SPRITE_NORMAL_DEFAULT = "KinitoNormal.png"
SPRITE_NORMAL2_DEFAULT = "KinitoNormal2.png"

# 8-way look directions derived from standing sprite filenames.
LOOK_DIRECTION_CENTER = "center"
LOOK_DIRECTIONS = (
    LOOK_DIRECTION_CENTER,
    "left",
    "right",
    "top",
    "bottom",
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
)

_STANDING_DIRECTION_SUFFIXES: dict[str, str] = {
    "": LOOK_DIRECTION_CENTER,
    "Left": "left",
    "Right": "right",
    "Top": "top",
    "Bottom": "bottom",
    "TopLeft": "top_left",
    "TopRight": "top_right",
    "BottomLeft": "bottom_left",
    "BottomRight": "bottom_right",
}

sprite_path_normal = os.path.join(sprites_standing_directory, SPRITE_NORMAL_DEFAULT)
sprite_path_normal_2 = os.path.join(sprites_standing2_directory, SPRITE_NORMAL2_DEFAULT)
sprite_path_idle = os.path.join(sprites_reading_directory, "Idle.png")
sprite_path_idle_2 = os.path.join(sprites_reading_directory, "Idle2.png")
sprite_path_idle_2_page = os.path.join(sprites_reading_directory, "Idle2Page.png")
sprite_path_idle_2_page_2 = os.path.join(sprites_reading_directory, "Idle2Page2.png")
sprite_path_idle_glasses = os.path.join(sprites_reading_directory, "IdleGlasses.png")
sprite_path_idle_glasses_2 = os.path.join(sprites_reading_directory, "IdleGlasses2.png")
sprite_path_idle_glasses_2_page = os.path.join(
    sprites_reading_directory, "IdleGlasses2Page.png"
)
sprite_path_idle_glasses_2_page_2 = os.path.join(
    sprites_reading_directory, "IdleGlasses2Page2.png"
)
sprite_path_fancy = os.path.join(sprites_magic_directory, "Fancy.png")
sprite_path_fancy_1 = os.path.join(sprites_magic_directory, "Fancy1.png")
sprite_path_surf_left = os.path.join(sprites_surfing_directory, "KinitoSurfLeft.png")
sprite_path_surf_right = os.path.join(sprites_surfing_directory, "KinitoSurfRight.png")
sprite_path_moving = sprite_path_surf_right
sprite_path_sleep = os.path.join(sprites_sleeping_directory, "Sleep.png")
sprite_path_sleep1 = os.path.join(sprites_sleeping_directory, "Sleep1.png")
sprite_path_sleep2 = os.path.join(sprites_sleeping_directory, "Sleep2.png")
sprite_path_sleep3 = os.path.join(sprites_sleeping_directory, "Sleep3.png")
sprite_path_talking = os.path.join(sprites_talking_directory, "Talking.png")
sprite_path_talking2 = os.path.join(sprites_talking_directory, "Talking2.png")
sprite_path_thinking = os.path.join(sprites_thinking_directory, "Thinking.png")
sprite_path_thinking2 = os.path.join(sprites_thinking_directory, "Thinking2.png")
sprite_path_hug = os.path.join(sprites_hugging_directory, "KinitoHug.png")
sprite_path_hug2 = os.path.join(sprites_hugging_directory, "KinitoHug2.png")

icon_path = os.path.join(icons_directory, "Icon.ico")
favicon_path = os.path.join(icons_directory, "Favicon.png")

crash_image_path = os.path.join(crash_directory, "blueScreen.png")
kinito_pet_url = "https://www.kinitopet.com/"

newbeginnings_file_path = os.path.join(sounds_directory, "NewBeginningsPoemEdit.mp3")
timer_file_path = os.path.join(sounds_directory, "Timer.mp3")
tune_file_path = os.path.join(sounds_directory, "TinyTune.mp3")
starttalk_file_path = os.path.join(sounds_directory, "StartTalking.mp3")
stoptalk_file_path = os.path.join(sounds_directory, "StopTalking.mp3")
woosh_file_path = os.path.join(sounds_directory, "Woosh.mp3")
surf_file_path = os.path.join(sounds_directory, "Surf.mp3")
bomp_file_path = os.path.join(sounds_directory, "Bomp.mp3")
page_turn_file_path = os.path.join(sounds_directory, "PageTurn.mp3")

_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")


def ensure_user_media_directories():
    """Create GameAssets/UserMedia for memory files if it does not exist yet."""
    os.makedirs(user_media_directory, exist_ok=True)


def list_image_files(directory):
    """Return absolute paths to image files inside *directory*."""
    if not os.path.isdir(directory):
        return []
    files = []
    for name in os.listdir(directory):
        if name.lower().endswith(_IMAGE_EXTENSIONS):
            files.append(os.path.join(directory, name))
    return sorted(files)


def list_standing_sprite_paths(*, crouch: bool = False) -> list[str]:
    """Return standing (or crouch) sprite paths with the default variant first."""
    if crouch:
        directory = sprites_standing2_directory
        default_name = SPRITE_NORMAL2_DEFAULT
    else:
        directory = sprites_standing_directory
        default_name = SPRITE_NORMAL_DEFAULT

    paths = list_image_files(directory)
    if not paths:
        return []

    default_path = os.path.join(directory, default_name)
    ordered = []
    if default_path in paths:
        ordered.append(default_path)
    for path in paths:
        if path != default_path:
            ordered.append(path)
    return ordered


def standing_direction_from_path(path: str) -> str | None:
    """Return a look-direction id from a standing/crouch sprite filename, or None."""
    stem = os.path.splitext(os.path.basename(path))[0]
    for prefix in ("KinitoNormal2", "KinitoNormal"):
        if stem.startswith(prefix):
            suffix = stem[len(prefix) :]
            return _STANDING_DIRECTION_SUFFIXES.get(suffix)
    return None


def look_direction_from_delta(dx: float, dy: float, *, deadzone_px: float) -> str:
    """Map a screen-space delta (y down) to an 8-way look direction."""
    if math.hypot(dx, dy) <= deadzone_px:
        return LOOK_DIRECTION_CENTER
    # atan2: 0=right, +90=down, ±180=left, -90=up (screen coordinates).
    degrees = math.degrees(math.atan2(dy, dx))
    if -22.5 <= degrees < 22.5:
        return "right"
    if 22.5 <= degrees < 67.5:
        return "bottom_right"
    if 67.5 <= degrees < 112.5:
        return "bottom"
    if 112.5 <= degrees < 157.5:
        return "bottom_left"
    if degrees >= 157.5 or degrees < -157.5:
        return "left"
    if -157.5 <= degrees < -112.5:
        return "top_left"
    if -112.5 <= degrees < -67.5:
        return "top"
    return "top_right"
