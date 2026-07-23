"""Rare surprise ad popups from GameAssets/ads/."""

import random
import threading

from content.ads_lines import AD_SURPRISE_LINES
from kinito.assets import ads_directory, list_image_files


class AdsMixin:
    """Occasionally show a small ad window with feigned surprise."""

    AD_POPUP_CHANCE = 1 / 750

    def maybe_trigger_random_ad(self) -> bool:
        """Roll for a rare ad popup; schedule on the Tk main thread if it hits."""
        if not getattr(self, "_screen_effects_enabled", True):
            return False
        if getattr(self, "_focus_mode", False):
            return False
        if getattr(self, "_is_game_active", lambda: False)():
            return False
        if self.paused or self.is_dragging or self._camera_active or self._browser_active:
            return False
        if random.random() >= self.AD_POPUP_CHANCE:
            return False
        self.root.after(0, self._show_random_ad_popup)
        return True

    def _show_random_ad_popup(self):
        """Open a small ad image window and comment with mock surprise."""
        if not self._running:
            return
        images = list_image_files(ads_directory)
        if not images:
            return
        image_path = random.choice(images)
        threading.Thread(
            target=self._present_ad_popup,
            args=(image_path,),
            daemon=True,
        ).start()

    def _present_ad_popup(self, image_path):
        """Speak a surprise line, then show the ad in a compact window."""
        self.speak(random.choice(AD_SURPRISE_LINES))
        if not self._running:
            return
        self.root.after(0, lambda: self.show_popup_image(image_path, title="KinitoPET Ad"))
