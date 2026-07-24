import os

import pytest

from kinito import assets


def test_assets_directory_is_under_project_root():
    assert assets.assets_directory.endswith("GameAssets")
    assert os.path.isabs(assets.assets_directory)


@pytest.mark.parametrize(
    "directory_attr,relative_path",
    [
        ("sprites_directory", os.path.join("GameAssets", "sprites")),
        ("icons_directory", os.path.join("GameAssets", "icons")),
        ("sounds_directory", os.path.join("GameAssets", "sounds")),
        ("secret_images_directory", os.path.join("GameAssets", "SecretImages")),
        ("programs_directory", os.path.join("GameAssets", "Programs")),
        ("ads_directory", os.path.join("GameAssets", "ads")),
        ("websites_directory", os.path.join("GameAssets", "websites")),
        ("crash_directory", os.path.join("GameAssets", "crash")),
    ],
)
def test_asset_subdirectories(directory_attr, relative_path):
    directory = getattr(assets, directory_attr)
    assert directory.endswith(relative_path)
    assert os.path.isabs(directory)
    assert assets.assets_directory in directory


@pytest.mark.parametrize(
    "path_attr,filename,parent_attr",
    [
        ("sprite_path_normal", "KinitoNormal.png", "sprites_standing_directory"),
        ("sprite_path_normal_2", "KinitoNormal2.png", "sprites_standing2_directory"),
        ("sprite_path_idle", "Idle.png", "sprites_reading_directory"),
        ("sprite_path_idle_2", "Idle2.png", "sprites_reading_directory"),
        ("sprite_path_idle_2_page", "Idle2Page.png", "sprites_reading_directory"),
        ("sprite_path_idle_2_page_2", "Idle2Page2.png", "sprites_reading_directory"),
        ("sprite_path_idle_glasses", "IdleGlasses.png", "sprites_reading_directory"),
        ("sprite_path_idle_glasses_2", "IdleGlasses2.png", "sprites_reading_directory"),
        (
            "sprite_path_idle_glasses_2_page",
            "IdleGlasses2Page.png",
            "sprites_reading_directory",
        ),
        (
            "sprite_path_idle_glasses_2_page_2",
            "IdleGlasses2Page2.png",
            "sprites_reading_directory",
        ),
        ("sprite_path_fancy", "Fancy.png", "sprites_magic_directory"),
        ("sprite_path_fancy_1", "Fancy1.png", "sprites_magic_directory"),
        ("sprite_path_surf_left", "KinitoSurfLeft.png", "sprites_surfing_directory"),
        ("sprite_path_surf_right", "KinitoSurfRight.png", "sprites_surfing_directory"),
        ("sprite_path_moving", "KinitoSurfRight.png", "sprites_surfing_directory"),
        ("sprite_path_sleep", "Sleep.png", "sprites_sleeping_directory"),
        ("sprite_path_sleep1", "Sleep1.png", "sprites_sleeping_directory"),
        ("sprite_path_sleep2", "Sleep2.png", "sprites_sleeping_directory"),
        ("sprite_path_sleep3", "Sleep3.png", "sprites_sleeping_directory"),
        ("sprite_path_talking", "Talking.png", "sprites_talking_directory"),
        ("sprite_path_talking2", "Talking2.png", "sprites_talking_directory"),
        ("sprite_path_thinking", "Thinking.png", "sprites_thinking_directory"),
        ("sprite_path_thinking2", "Thinking2.png", "sprites_thinking_directory"),
        ("sprite_path_hug", "KinitoHug.png", "sprites_hugging_directory"),
        ("sprite_path_hug2", "KinitoHug2.png", "sprites_hugging_directory"),
        ("crash_image_path", "blueScreen.png", "crash_directory"),
        ("page_turn_file_path", "PageTurn.mp3", "sounds_directory"),
        ("icon_path", "Icon.ico", "icons_directory"),
        ("favicon_path", "Favicon.png", "icons_directory"),
        ("timer_file_path", "Timer.mp3", "sounds_directory"),
        ("stoptalk_file_path", "StopTalking.mp3", "sounds_directory"),
        ("woosh_file_path", "Woosh.mp3", "sounds_directory"),
        ("surf_file_path", "Surf.mp3", "sounds_directory"),
        ("bomp_file_path", "Bomp.mp3", "sounds_directory"),
        ("tune_file_path", "TinyTune.mp3", "sounds_directory"),
        ("newbeginnings_file_path", "NewBeginningsPoemEdit.mp3", "sounds_directory"),
        ("balconexe_directory", "balcon.exe", "programs_directory"),
    ],
)
def test_asset_paths_point_to_expected_files(path_attr, filename, parent_attr):
    path = getattr(assets, path_attr)
    parent = getattr(assets, parent_attr)
    assert path.endswith(filename)
    assert parent in path


@pytest.mark.parametrize(
    "path_attr",
    [
        "sprite_path_normal",
        "sprite_path_normal_2",
        "sprite_path_idle",
        "sprite_path_idle_2",
        "sprite_path_fancy",
        "sprite_path_fancy_1",
        "sprite_path_surf_left",
        "sprite_path_surf_right",
        "sprite_path_moving",
        "sprite_path_sleep",
        "sprite_path_sleep1",
        "sprite_path_sleep2",
        "sprite_path_sleep3",
        "sprite_path_talking",
        "sprite_path_talking2",
        "sprite_path_thinking",
        "sprite_path_thinking2",
        "sprite_path_hug",
        "sprite_path_hug2",
    ],
)
def test_sprite_paths_stay_under_sprites_directory(path_attr):
    path = getattr(assets, path_attr)
    assert path.startswith(assets.sprites_directory + os.sep)


@pytest.mark.parametrize(
    "path_attr",
    ["icon_path", "favicon_path"],
)
def test_icon_paths_stay_under_icons_directory(path_attr):
    path = getattr(assets, path_attr)
    assert path.startswith(assets.icons_directory + os.sep)


@pytest.mark.parametrize(
    "path_attr",
    [
        "timer_file_path",
        "starttalk_file_path",
        "stoptalk_file_path",
        "woosh_file_path",
        "surf_file_path",
        "bomp_file_path",
        "tune_file_path",
        "newbeginnings_file_path",
        "page_turn_file_path",
    ],
)
def test_sound_paths_stay_under_sounds_directory(path_attr):
    path = getattr(assets, path_attr)
    assert path.startswith(assets.sounds_directory + os.sep)


def test_list_image_files_returns_sorted_paths(tmp_path):
    for name in ("b.png", "a.webp", "notes.txt"):
        (tmp_path / name).write_bytes(b"x")
    files = assets.list_image_files(str(tmp_path))
    assert len(files) == 2
    assert files[0].endswith("a.webp")
    assert files[1].endswith("b.png")


@pytest.mark.skipif(
    not os.path.isdir(assets.sprites_standing_directory),
    reason="Standing sprites folder is not present in this checkout",
)
def test_list_standing_sprite_paths_puts_default_first():
    paths = assets.list_standing_sprite_paths(crouch=False)
    assert paths
    assert paths[0] == assets.sprite_path_normal
    assert len(paths) >= 2

    crouch_paths = assets.list_standing_sprite_paths(crouch=True)
    assert crouch_paths
    assert crouch_paths[0] == assets.sprite_path_normal_2
    assert len(crouch_paths) >= 2


@pytest.mark.parametrize(
    "filename,direction",
    [
        ("KinitoNormal.png", "center"),
        ("KinitoNormalLeft.png", "left"),
        ("KinitoNormalRight.png", "right"),
        ("KinitoNormalTop.png", "top"),
        ("KinitoNormalBottom.png", "bottom"),
        ("KinitoNormalTopLeft.png", "top_left"),
        ("KinitoNormalTopRight.png", "top_right"),
        ("KinitoNormalBottomLeft.png", "bottom_left"),
        ("KinitoNormalBottomRight.png", "bottom_right"),
        ("KinitoNormal2.png", "center"),
        ("KinitoNormal2Left.png", "left"),
        ("KinitoNormal2TopRight.png", "top_right"),
    ],
)
def test_standing_direction_from_path(filename, direction):
    assert assets.standing_direction_from_path(f"/sprites/{filename}") == direction


def test_standing_direction_from_path_rejects_unknown():
    assert assets.standing_direction_from_path("/sprites/Fancy.png") is None


@pytest.mark.parametrize(
    "dx,dy,expected",
    [
        (0, 0, "center"),
        (10, 0, "center"),  # inside deadzone
        (100, 0, "right"),
        (-100, 0, "left"),
        (0, -100, "top"),
        (0, 100, "bottom"),
        (100, -100, "top_right"),
        (-100, 100, "bottom_left"),
    ],
)
def test_look_direction_from_delta(dx, dy, expected):
    assert assets.look_direction_from_delta(dx, dy, deadzone_px=40) == expected


@pytest.mark.skipif(
    not os.path.isdir(assets.assets_directory),
    reason="GameAssets folder is not present in this checkout",
)
def test_packaged_asset_files_exist_on_disk():
    expected_files = [
        assets.sprite_path_normal,
        assets.sprite_path_normal_2,
        assets.sprite_path_idle,
        assets.sprite_path_idle_2,
        assets.sprite_path_idle_2_page,
        assets.sprite_path_idle_2_page_2,
        assets.sprite_path_idle_glasses,
        assets.sprite_path_idle_glasses_2_page,
        assets.sprite_path_fancy_1,
        assets.crash_image_path,
        assets.page_turn_file_path,
        assets.icon_path,
        assets.favicon_path,
        assets.timer_file_path,
        assets.starttalk_file_path,
        assets.balconexe_directory,
    ]
    missing = [path for path in expected_files if not os.path.isfile(path)]
    assert missing == []
