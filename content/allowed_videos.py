# Curated video whitelist — manually checked: no gore, illegal, or pornographic content.
# These URLs open in Kinito's small browser window (HTTPS pages with embedded video).
ALLOWED_VIDEOS = {
    "nature": [
        {
            "title": "NASA — Earth at Night",
            "url": "https://science.nasa.gov/earth/earth-at-night/",
        },
        {
            "title": "NASA — Our Living Planet",
            "url": "https://science.nasa.gov/earth/facts/",
        },
        {
            "title": "National Geographic — Environment",
            "url": "https://www.nationalgeographic.com/environment",
        },
    ],
    "animals": [
        {
            "title": "San Diego Zoo — Live Cams",
            "url": "https://zoo.sandiegozoo.org/live-cams",
        },
        {
            "title": "Monterey Bay Aquarium — Live Cams",
            "url": "https://www.montereybayaquarium.org/animals/live-cams",
        },
        {
            "title": "National Geographic — Animals",
            "url": "https://www.nationalgeographic.com/animals",
        },
    ],
    "space": [
        {
            "title": "NASA — Image of the Day",
            "url": "https://www.nasa.gov/multimedia/imagegallery/index.html",
        },
        {
            "title": "NASA Space Place",
            "url": "https://spaceplace.nasa.gov/",
        },
        {
            "title": "Hubble — Gallery",
            "url": "https://science.nasa.gov/mission/hubble/multimedia/",
        },
    ],
}

VIDEO_CATEGORIES = list(ALLOWED_VIDEOS.keys())
