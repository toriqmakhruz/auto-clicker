"""
Macro Engine - Background Click Recorder & Replayer
Mengatur perekaman klik mouse, playback otomatis, global hotkeys, dan penyimpanan skrip.
"""

import time
import json
import threading
import ctypes
from ctypes import wintypes
from typing import List, Dict, Any, Callable, Optional
from pynput import mouse, keyboard

# Set DPI Awareness agar koordinat mouse akurat di semua resolusi dan display scaling Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Win32 Mouse Event Constants
MOUSEEVENTF_LEFTDOWN   = 0x0002
MOUSEEVENTF_LEFTUP     = 0x0004
MOUSEEVENTF_RIGHTDOWN  = 0x0008
MOUSEEVENTF_RIGHTUP    = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP   = 0x0040

def win32_click(x: int, y: int, action: str = "left"):
    """Melakukan klik pada koordinat (x, y) menggunakan Windows API langsung."""
    user32 = ctypes.windll.user32
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.02)
    
    if action == "left":
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.03)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif action == "right":
        user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.03)
        user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    elif action == "double":
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(0.06)
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif action == "middle":
        user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
        time.sleep(0.03)
        user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)

def get_current_cursor_pos():
    """Mengambil koordinat kursor saat ini via GetCursorPos."""
    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return int(pt.x), int(pt.y)


class MacroStep:
    """Mewakili 1 langkah klik dalam skrip makro."""
    def __init__(self, x: int, y: int, action: str = "left", delay: float = 1.0, note: str = ""):
        self.x = int(x)
        self.y = int(y)
        self.action = action  # 'left', 'right', 'double', 'middle'
        self.delay = max(0.0, float(delay))  # jeda dalam detik sebelum klik
        self.note = str(note)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "action": self.action,
            "delay": round(self.delay, 2),
            "note": self.note
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MacroStep":
        return cls(
            x=data.get("x", 0),
            y=data.get("y", 0),
            action=data.get("action", "left"),
            delay=data.get("delay", 1.0),
            note=data.get("note", "")
        )


class MacroEngine:
    """Engine utama untuk merekam dan memutar klik otomatis di background."""
    def __init__(self):
        self.steps: List[MacroStep] = []
        self.is_recording = False
        self.is_playing = False
        self.is_paused = False
        self._stop_requested = False
        
        # Pengaturan playback
        self.loop_count = 1  # 0 berarti looping tak terbatas (infinite)
        self.loop_delay = 1.0  # Jeda antar pengulangan loop (detik)
        self.record_mode = "realtime"  # 'realtime' (jeda asli) atau 'fixed' (jeda tetap)
        self.fixed_delay_value = 1.0

        # Koordinat window GUI untuk mengabaikan klik pada aplikasi itu sendiri saat merekam
        self.window_bbox = None  # (x1, y1, x2, y2)

        # Threading & listeners
        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._play_thread: Optional[threading.Thread] = None
        self._last_click_time: Optional[float] = None

        # Callbacks untuk integrasi GUI
        self.on_step_added: Optional[Callable[[MacroStep, int], None]] = None
        self.on_playback_step: Optional[Callable[[int, int], None]] = None  # (step_idx, loop_idx)
        self.on_state_changed: Optional[Callable[[str, str], None]] = None  # (state, message)

        self._start_global_hotkeys()

    def set_window_bbox(self, bbox: Optional[tuple]):
        """Menyimpan batas window UI agar klik pada UI tidak ikut terekam."""
        self.window_bbox = bbox

    def _notify_state(self, state: str, message: str = ""):
        if self.on_state_changed:
            self.on_state_changed(state, message)

    # ------------------ GLOBAL HOTKEYS ------------------
    def _start_global_hotkeys(self):
        """Memulai listener keyboard global agar bisa F6, F7, F8 dari background."""
        def on_press(key):
            try:
                if key == keyboard.Key.f6:
                    # Toggle Rekam
                    if self.is_recording:
                        self.stop_recording()
                    elif not self.is_playing:
                        self.start_recording()
                elif key == keyboard.Key.f7:
                    # Toggle Play / Pause
                    if self.is_playing:
                        self.toggle_pause()
                    elif not self.is_recording:
                        self.start_playback()
                elif key == keyboard.Key.f8:
                    # Emergency Stop
                    self.stop_all()
            except Exception as e:
                print(f"Error in hotkey handler: {e}")

        self._keyboard_listener = keyboard.Listener(on_press=on_press)
        self._keyboard_listener.daemon = True
        self._keyboard_listener.start()

    # ------------------ PEREKAMAN (RECORDING) ------------------
    def start_recording(self, append: bool = True):
        """Mulai merekam klik mouse."""
        if self.is_playing:
            return
        if not append:
            self.steps.clear()
        
        self.is_recording = True
        self._last_click_time = time.time()
        self._notify_state("recording", "Perekaman aktif! Klik di layar mana saja. Tekan F6 untuk selesai.")

        def on_click(x, y, button, pressed):
            if not self.is_recording:
                return False
            
            # Hanya rekam saat tombol mouse ditekan (pressed)
            if pressed:
                # Cek apakah klik berada di dalam window Auto Clicker
                if self.window_bbox:
                    wx1, wy1, wx2, wy2 = self.window_bbox
                    if wx1 <= x <= wx2 and wy1 <= y <= wy2:
                        # Abaikan klik di dalam UI aplikasi sendiri
                        return

                now = time.time()
                if self.record_mode == "realtime":
                    delay = round(max(0.1, now - self._last_click_time), 2)
                    # Jika step pertama, berikan jeda awal wajar (misal 1 detik)
                    if len(self.steps) == 0:
                        delay = 1.0
                else:
                    delay = round(self.fixed_delay_value, 2)

                self._last_click_time = now

                # Tentukan jenis klik
                action = "left"
                if button == mouse.Button.right:
                    action = "right"
                elif button == mouse.Button.middle:
                    action = "middle"

                step = MacroStep(x=int(x), y=int(y), action=action, delay=delay)
                self.steps.append(step)

                if self.on_step_added:
                    self.on_step_added(step, len(self.steps) - 1)

        self._mouse_listener = mouse.Listener(on_click=on_click)
        self._mouse_listener.daemon = True
        self._mouse_listener.start()

    def stop_recording(self):
        """Hentikan proses perekaman."""
        if not self.is_recording:
            return
        self.is_recording = False
        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
            self._mouse_listener = None
        self._notify_state("idle", f"Perekaman selesai. Total {len(self.steps)} langkah tersimpan.")

    # ------------------ PEMUTARAN (PLAYBACK) ------------------
    def start_playback(self):
        """Mulai memutar langkah-langkah yang sudah terekam."""
        if self.is_recording or self.is_playing:
            return
        if not self.steps:
            self._notify_state("idle", "Tidak ada langkah untuk dijalankan. Rekam terlebih dahulu!")
            return

        self.is_playing = True
        self.is_paused = False
        self._stop_requested = False
        self._notify_state("playing", "Playback berjalan... Tekan F7 untuk Jeda, F8 untuk Stop darurat.")

        self._play_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self._play_thread.start()

    def toggle_pause(self):
        """Jeda atau lanjutkan playback."""
        if not self.is_playing:
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self._notify_state("paused", "Playback DIJEDA (Paused). Tekan F7 untuk melanjutkan.")
        else:
            self._notify_state("playing", "Playback DILANJUTKAN. Tekan F8 untuk Stop.")

    def stop_all(self):
        """Hentikan semua proses secara darurat (F8)."""
        self._stop_requested = True
        if self.is_recording:
            self.stop_recording()
        if self.is_playing:
            self.is_playing = False
            self.is_paused = False
            self._notify_state("idle", "Playback dihentikan (Emergency Stop).")

    def _interruptible_sleep(self, seconds: float) -> bool:
        """Tidur dengan interval kecil agar tombol Stop (F8) langsung merespons seketika."""
        step_time = 0.04
        elapsed = 0.0
        while elapsed < seconds:
            if self._stop_requested:
                return False
            while self.is_paused and not self._stop_requested:
                time.sleep(0.08)
            time.sleep(min(step_time, seconds - elapsed))
            elapsed += step_time
        return not self._stop_requested

    def _playback_worker(self):
        """Background thread yang mengeksekusi klik demi klik."""
        loop_counter = 0
        total_loops = self.loop_count  # 0 = infinite

        try:
            while not self._stop_requested:
                loop_counter += 1
                
                for idx, step in enumerate(self.steps):
                    if self._stop_requested:
                        break

                    # Update UI langkah aktif
                    if self.on_playback_step:
                        self.on_playback_step(idx, loop_counter)

                    # Tunggu sesuai jeda waktu step ini
                    if not self._interruptible_sleep(step.delay):
                        break

                    # Lakukan klik
                    win32_click(step.x, step.y, step.action)

                if self._stop_requested:
                    break

                # Cek apakah looping sudah selesai
                if total_loops > 0 and loop_counter >= total_loops:
                    break

                # Jeda antar loop
                if not self._interruptible_sleep(self.loop_delay):
                    break

        except Exception as e:
            print(f"Error during playback: {e}")
        finally:
            self.is_playing = False
            self.is_paused = False
            if self._stop_requested:
                self._notify_state("idle", "Playback dihentikan.")
            else:
                self._notify_state("idle", f"Playback selesai seluruhnya ({loop_counter} putaran).")
            if self.on_playback_step:
                self.on_playback_step(-1, loop_counter)

    # ------------------ MANAJEMEN LANGKAH & FILE ------------------
    def add_step(self, x: int, y: int, action: str = "left", delay: float = 1.0, note: str = ""):
        """Tambah langkah manual."""
        step = MacroStep(x, y, action, delay, note)
        self.steps.append(step)
        if self.on_step_added:
            self.on_step_added(step, len(self.steps) - 1)
        return step

    def remove_step(self, index: int):
        """Hapus langkah pada index tertentu."""
        if 0 <= index < len(self.steps):
            self.steps.pop(index)

    def clear_steps(self):
        """Kosongkan semua langkah."""
        self.steps.clear()

    def test_single_step(self, index: int):
        """Tes eksekusi 1 klik saja untuk memastikan posisi tepat."""
        if 0 <= index < len(self.steps):
            step = self.steps[index]
            threading.Thread(target=lambda: win32_click(step.x, step.y, step.action), daemon=True).start()

    def save_to_file(self, filepath: str):
        """Simpan rekaman ke file JSON."""
        data = {
            "version": "1.0",
            "loop_count": self.loop_count,
            "loop_delay": self.loop_delay,
            "record_mode": self.record_mode,
            "fixed_delay_value": self.fixed_delay_value,
            "steps": [step.to_dict() for step in self.steps]
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_from_file(self, filepath: str):
        """Muat skrip rekaman dari file JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.loop_count = data.get("loop_count", 1)
        self.loop_delay = data.get("loop_delay", 1.0)
        self.record_mode = data.get("record_mode", "realtime")
        self.fixed_delay_value = data.get("fixed_delay_value", 1.0)
        
        self.steps = [MacroStep.from_dict(item) for item in data.get("steps", [])]
        return self.steps
