"""Local microphone capture, silence detection, and Whisper transcription."""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from typing import Any

SAMPLE_RATE = 16_000
CHANNELS = 1
CHUNK_MS = 100
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_MS // 1000
DEFAULT_SILENCE_MS = 1000
DEFAULT_MIN_SPEECH_MS = 200
DEFAULT_SPEECH_RMS = 0.004
DEFAULT_MAX_UTTERANCE_MS = 15_000
DEFAULT_NOISE_CALIBRATION_CHUNKS = 8
WHISPER_MODEL_SIZE = "tiny"
WHISPER_REPO_ID = "Systran/faster-whisper-tiny"


def _numpy():
    """Import numpy lazily so the app can start without STT deps."""
    import numpy as np

    return np


def whisper_model_directory() -> str:
    """Return the on-disk cache folder for the faster-whisper tiny model."""
    from kinito.assets import user_media_directory

    return os.path.join(user_media_directory, "models", "faster-whisper-tiny")


class SilenceDetector:
    """Track speech energy and decide when an utterance is finished."""

    def __init__(
        self,
        *,
        silence_ms: int = DEFAULT_SILENCE_MS,
        min_speech_ms: int = DEFAULT_MIN_SPEECH_MS,
        speech_rms: float = DEFAULT_SPEECH_RMS,
        chunk_ms: int = CHUNK_MS,
        max_utterance_ms: int = DEFAULT_MAX_UTTERANCE_MS,
        calibration_chunks: int = DEFAULT_NOISE_CALIBRATION_CHUNKS,
    ) -> None:
        self._silence_chunks = max(1, silence_ms // chunk_ms)
        self._min_speech_chunks = max(1, min_speech_ms // chunk_ms)
        self._base_speech_rms = speech_rms
        self._speech_rms = speech_rms
        self._max_chunks = max(1, max_utterance_ms // chunk_ms)
        self._calibration_chunks = max(1, calibration_chunks)
        self.reset()

    def reset(self) -> None:
        """Clear utterance state for a new listen session."""
        self._speech_chunks = 0
        self._silence_after_speech = 0
        self._total_chunks = 0
        self._started = False
        self._noise_levels: list[float] = []
        self._speech_rms = self._base_speech_rms

    @staticmethod
    def rms(chunk) -> float:
        """Return root-mean-square energy for a mono float chunk."""
        np = _numpy()
        arr = np.asarray(chunk, dtype=np.float64).reshape(-1)
        if arr.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(arr))))

    def feed(self, chunk) -> str | None:
        """Feed one audio chunk.

        Returns:
            ``None`` to keep listening, ``"finalize"`` when the utterance is done.
        """
        self._total_chunks += 1
        level = self.rms(chunk)

        if len(self._noise_levels) < self._calibration_chunks and not self._started:
            self._noise_levels.append(level)
            if len(self._noise_levels) == self._calibration_chunks:
                noise_floor = sorted(self._noise_levels)[len(self._noise_levels) // 2]
                self._speech_rms = max(self._base_speech_rms, noise_floor * 4.0)

        if level >= self._speech_rms:
            self._started = True
            self._speech_chunks += 1
            self._silence_after_speech = 0
        elif self._started:
            self._silence_after_speech += 1

        # Always stop after the absolute max, even with no speech detected.
        if self._total_chunks >= self._max_chunks:
            return "finalize"

        if (
            self._started
            and self._speech_chunks >= self._min_speech_chunks
            and self._silence_after_speech >= self._silence_chunks
        ):
            return "finalize"
        return None


_whisper_model: Any | None = None
_whisper_lock = threading.Lock()


def check_voice_input_available() -> tuple[bool, str | None]:
    """Return whether local STT dependencies import cleanly."""
    try:
        import numpy  # noqa: F401
        import sounddevice  # noqa: F401
        from faster_whisper import WhisperModel  # noqa: F401
    except ImportError as exc:
        return False, str(exc)
    return True, None


def _configure_insecure_hf_backend() -> Callable[[], None]:
    """Disable TLS verification for Hugging Face downloads (corporate proxies).

    Returns a restore callback.
    """
    try:
        import requests
        from huggingface_hub import configure_http_backend
    except ImportError:
        return lambda: None

    def factory():
        session = requests.Session()
        session.verify = False
        return session

    try:
        configure_http_backend(backend_factory=factory)
    except Exception:  # noqa: BLE001
        return lambda: None

    def restore() -> None:
        try:
            configure_http_backend()
        except Exception:  # noqa: BLE001
            pass

    return restore


def _ensure_whisper_files() -> str:
    """Download the tiny model into UserMedia if needed; return local path."""
    local_dir = whisper_model_directory()
    os.makedirs(local_dir, exist_ok=True)
    marker = os.path.join(local_dir, "model.bin")
    if os.path.isfile(marker):
        return local_dir

    from huggingface_hub import snapshot_download

    print(f"Kinito: downloading Whisper model to {local_dir} ...", flush=True)
    try:
        snapshot_download(
            repo_id=WHISPER_REPO_ID,
            local_dir=local_dir,
        )
    except Exception as first_exc:  # noqa: BLE001
        print(
            f"Kinito: Whisper download failed ({first_exc!r}); "
            "retrying with SSL verification disabled.",
            flush=True,
        )
        restore = _configure_insecure_hf_backend()
        try:
            snapshot_download(
                repo_id=WHISPER_REPO_ID,
                local_dir=local_dir,
            )
        finally:
            restore()
    if not os.path.isfile(marker):
        # Some snapshots name the weights differently; accept config as proof.
        config = os.path.join(local_dir, "config.json")
        if not os.path.isfile(config):
            raise FileNotFoundError(
                f"Whisper model files missing after download in {local_dir}"
            )
    print("Kinito: Whisper model ready.", flush=True)
    return local_dir


def _get_whisper_model():
    """Lazy-load a shared faster-whisper model (CPU int8)."""
    global _whisper_model
    with _whisper_lock:
        if _whisper_model is None:
            from faster_whisper import WhisperModel

            model_path = _ensure_whisper_files()
            _whisper_model = WhisperModel(
                model_path,
                device="cpu",
                compute_type="int8",
            )
        return _whisper_model


def normalize_audio_levels(audio):
    """Boost quiet microphone captures toward a usable peak for Whisper."""
    np = _numpy()
    samples = np.asarray(audio, dtype=np.float32).reshape(-1)
    if samples.size == 0:
        return samples
    peak = float(np.max(np.abs(samples)))
    if peak <= 1e-8:
        return samples
    if peak < 0.15:
        samples = samples * (0.4 / peak)
        samples = np.clip(samples, -1.0, 1.0)
    return samples


def transcribe_audio(
    audio,
    *,
    sample_rate: int = SAMPLE_RATE,
    language: str | None = None,
) -> str:
    """Transcribe mono float32 audio with faster-whisper."""
    del sample_rate  # WhisperModel.transcribe expects samples at model rate
    samples = normalize_audio_levels(audio)
    if samples.size == 0:
        return ""
    model = _get_whisper_model()
    segments, _info = model.transcribe(
        samples,
        language=language,
        beam_size=1,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    parts = [segment.text.strip() for segment in segments if segment.text.strip()]
    return " ".join(parts).strip()


class VoiceInputController:
    """Capture one utterance from the default mic, then transcribe it.

    Each ``start()`` listens until silence (or stop), then invokes
    ``on_final_text`` / ``on_error`` on the UI thread via ``schedule``.
    """

    def __init__(
        self,
        *,
        schedule: Callable[[Callable[[], None]], None],
        on_final_text: Callable[[str], None],
        on_error: Callable[[str], None],
        silence_ms: int = DEFAULT_SILENCE_MS,
        speech_rms: float = DEFAULT_SPEECH_RMS,
    ) -> None:
        self._schedule = schedule
        self._on_final_text = on_final_text
        self._on_error = on_error
        self._silence_ms = silence_ms
        self._speech_rms = speech_rms
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._listening = False
        self._lock = threading.Lock()

    @property
    def listening(self) -> bool:
        """Return whether a capture thread is active."""
        return self._listening

    def start(self) -> bool:
        """Begin capturing one utterance. Returns False if already listening."""
        with self._lock:
            if self._listening:
                return False
            available, err = check_voice_input_available()
            if not available:
                self._schedule(lambda: self._on_error(err or "unavailable"))
                return False
            self._stop_event.clear()
            self._listening = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            return True

    def stop(self) -> None:
        """Request the capture thread to stop without sending a transcript."""
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1.5)
        with self._lock:
            self._listening = False
            self._thread = None

    def _run(self) -> None:
        np = _numpy()
        frames: list = []
        detector = SilenceDetector(
            silence_ms=self._silence_ms,
            speech_rms=self._speech_rms,
        )
        stream = None
        try:
            # Fail fast if the model cannot be loaded/downloaded.
            _get_whisper_model()
            if self._stop_event.is_set():
                with self._lock:
                    self._listening = False
                    self._thread = None
                return

            import sounddevice as sd

            stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                blocksize=CHUNK_SAMPLES,
            )
            stream.start()
            while not self._stop_event.is_set():
                chunk, _overflowed = stream.read(CHUNK_SAMPLES)
                mono = np.asarray(chunk, dtype=np.float32).reshape(-1)
                frames.append(mono.copy())
                if detector.feed(mono) == "finalize":
                    break
        except Exception as exc:  # noqa: BLE001 — surface any mic/runtime failure to UI
            message = str(exc) or exc.__class__.__name__
            print(f"Kinito voice STT error: {message}", flush=True)
            self._schedule(lambda msg=message: self._on_error(msg))
            with self._lock:
                self._listening = False
                self._thread = None
            return
        finally:
            if stream is not None:
                try:
                    stream.stop()
                    stream.close()
                except Exception:  # noqa: BLE001
                    pass

        cancelled = self._stop_event.is_set()
        with self._lock:
            self._listening = False
            self._thread = None

        if cancelled:
            return

        if not frames:
            self._schedule(lambda: self._on_final_text(""))
            return

        audio = np.concatenate(frames)
        try:
            text = transcribe_audio(audio)
        except Exception as exc:  # noqa: BLE001
            message = str(exc) or exc.__class__.__name__
            print(f"Kinito voice STT error: {message}", flush=True)
            self._schedule(lambda msg=message: self._on_error(msg))
            return
        self._schedule(lambda: self._on_final_text(text))
