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

        def wm_attributes(self, *_args, **_kwargs):
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
        patch("kinito.features.programs.Toplevel", return_value=FakePopup()),
        patch("kinito.features.programs.apply_window_icon"),
        patch("kinito.features.programs.Label", MagicMock()),
        patch("kinito.features.programs.ImageTk.PhotoImage", MagicMock()),
    ):
        stub.show_popup_image(str(path), title="KinitoPET Ad")

    assert geometries
    assert geometries[-1].startswith("800x400+")
