"""Tests for dynamic popup image sizing."""

from unittest.mock import MagicMock, patch

from PIL import Image

from kinito.features.programs import ProgramsMixin


class ProgramsStub(ProgramsMixin):
    pass


def test_show_popup_image_sizes_window_to_image(tmp_path):
    stub = ProgramsStub()
    stub.root = MagicMock()
    stub.root.winfo_vrootx.return_value = 0
    stub.root.winfo_vrooty.return_value = 0
    stub.root.winfo_vrootwidth.return_value = 1920
    stub.root.winfo_vrootheight.return_value = 1080
    stub.root.update_idletasks = MagicMock()

    path = tmp_path / "ad.webp"
    Image.new("RGB", (800, 400), (20, 180, 40)).save(path)

    geometries = []

    class FakePopup:
        def title(self, *_args):
            return None

        def withdraw(self):
            return None

        def attributes(self, *_args, **_kwargs):
            return None

        def wm_attributes(self, *_args, **_kwargs):
            return None

        def deiconify(self):
            return None

        def configure(self, **_kwargs):
            return None

        def geometry(self, value):
            geometries.append(value)

        def protocol(self, *_args):
            return None

        def wait_window(self, *_args):
            return None

        def destroy(self):
            return None

    with (
        patch(
            "kinito.features.programs.create_staged_toplevel",
            return_value=FakePopup(),
        ),
        patch("kinito.features.programs.apply_window_icon"),
        patch("kinito.features.programs.Label", MagicMock()),
        patch("kinito.features.programs.ImageTk.PhotoImage", MagicMock()),
    ):
        stub.show_popup_image(str(path), title="KinitoPET Ad")

    assert geometries
    assert geometries[-1].startswith("800x400+")


def test_show_popup_image_upscales_tiny_ads_to_min_long_edge(tmp_path):
    stub = ProgramsStub()
    stub.root = MagicMock()
    stub.root.winfo_vrootx.return_value = 0
    stub.root.winfo_vrooty.return_value = 0
    stub.root.winfo_vrootwidth.return_value = 1920
    stub.root.winfo_vrootheight.return_value = 1080
    stub.root.update_idletasks = MagicMock()

    path = tmp_path / "tiny_ad.webp"
    Image.new("RGB", (185, 76), (20, 180, 40)).save(path)

    geometries = []

    class FakePopup:
        def title(self, *_args):
            return None

        def withdraw(self):
            return None

        def attributes(self, *_args, **_kwargs):
            return None

        def wm_attributes(self, *_args, **_kwargs):
            return None

        def deiconify(self):
            return None

        def configure(self, **_kwargs):
            return None

        def geometry(self, value):
            geometries.append(value)

        def protocol(self, *_args):
            return None

        def wait_window(self, *_args):
            return None

        def destroy(self):
            return None

    with (
        patch(
            "kinito.features.programs.create_staged_toplevel",
            return_value=FakePopup(),
        ),
        patch("kinito.features.programs.apply_window_icon"),
        patch("kinito.features.programs.Label", MagicMock()),
        patch("kinito.features.programs.ImageTk.PhotoImage", MagicMock()),
    ):
        stub.show_popup_image(str(path), title="KinitoPET Ad", min_long_edge=520)

    assert geometries
    # 185x76 → long edge 520 → ~520x213
    assert geometries[-1].startswith("520x213+")


def test_show_popup_image_random_position_uses_monitors(tmp_path):
    stub = ProgramsStub()
    stub.root = MagicMock()
    stub.root.winfo_vrootx.return_value = 0
    stub.root.winfo_vrooty.return_value = 0
    stub.root.winfo_vrootwidth.return_value = 1920
    stub.root.winfo_vrootheight.return_value = 1080
    stub.root.update_idletasks = MagicMock()

    path = tmp_path / "ad.webp"
    Image.new("RGB", (200, 100), (20, 180, 40)).save(path)

    geometries = []

    class FakePopup:
        def title(self, *_args):
            return None

        def withdraw(self):
            return None

        def attributes(self, *_args, **_kwargs):
            return None

        def wm_attributes(self, *_args, **_kwargs):
            return None

        def deiconify(self):
            return None

        def configure(self, **_kwargs):
            return None

        def geometry(self, value):
            geometries.append(value)

        def protocol(self, *_args):
            return None

        def wait_window(self, *_args):
            return None

        def destroy(self):
            return None

    with (
        patch(
            "kinito.features.programs.create_staged_toplevel",
            return_value=FakePopup(),
        ),
        patch("kinito.features.programs.apply_window_icon"),
        patch("kinito.features.programs.Label", MagicMock()),
        patch("kinito.features.programs.ImageTk.PhotoImage", MagicMock()),
        patch(
            "kinito.features.programs.random_fully_visible_origin",
            return_value=(123, 456),
        ) as pick_origin,
        patch(
            "kinito.features.programs.list_monitor_rects",
            return_value=[(0, 0, 1920, 1080)],
        ),
    ):
        stub.show_popup_image(str(path), title="KinitoPET Ad", random_position=True)

    pick_origin.assert_called_once()
    assert geometries[-1] == "200x100+123+456"
