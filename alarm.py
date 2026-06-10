import math
import struct
import threading
import time
import wave

from config import ALARM_SOUND_PATH, ASSETS_DIR


def ensure_alarm_sound() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if ALARM_SOUND_PATH.exists():
        return

    sample_rate = 22050
    duration_sec = 0.5
    frequency = 880.0
    amplitude = 32000
    num_samples = int(sample_rate * duration_sec)

    with wave.open(str(ALARM_SOUND_PATH), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for i in range(num_samples):
            value = int(
                amplitude * math.sin(2.0 * math.pi * frequency * i / sample_rate)
            )
            wav_file.writeframes(struct.pack("<h", value))


class AlarmManager:
    def __init__(self) -> None:
        ensure_alarm_sound()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._active = False
        self._sound_handle = None

    @property
    def is_active(self) -> bool:
        return self._active

    def start(self) -> None:
        if self._active:
            return
        self._active = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="FocusTrackAlarm", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._active:
            return
        self._stop_event.set()
        self._silence()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._thread = None
        self._active = False

    def _start_loop(self) -> None:
        import winsound

        winsound.PlaySound(
            str(ALARM_SOUND_PATH),
            winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP,
        )

    def _silence(self) -> None:
        try:
            import winsound

            winsound.PlaySound(None, winsound.SND_PURGE)
        except RuntimeError:
            pass

        if self._sound_handle is not None:
            try:
                self._sound_handle.stop()
            except Exception:
                pass
            self._sound_handle = None

    def _run_fallback_loop(self) -> None:
        from playsound3 import playsound

        clip_duration = 0.5
        try:
            with wave.open(str(ALARM_SOUND_PATH), "r") as wav_file:
                clip_duration = wav_file.getnframes() / float(wav_file.getframerate())
        except wave.Error:
            pass

        while not self._stop_event.is_set():
            try:
                self._sound_handle = playsound(str(ALARM_SOUND_PATH), block=False)
            except Exception:
                print("[alarm] Could not play alarm.wav")
                break
            if self._stop_event.wait(timeout=max(clip_duration, 0.1)):
                break

    def _run(self) -> None:
        try:
            try:
                self._start_loop()
            except RuntimeError:
                self._run_fallback_loop()
                return

            while not self._stop_event.is_set():
                time.sleep(0.25)
        finally:
            self._silence()
