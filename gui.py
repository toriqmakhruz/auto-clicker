"""
GUI - Tampilan Antarmuka Auto Clicker Macro Modern
Menggunakan CustomTkinter untuk antarmuka yang bersih, responsif, dan mudah digunakan.
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from macro_engine import MacroEngine, MacroStep, get_current_cursor_pos

# Setup tema CustomTkinter
ctk.set_appearance_mode("System")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

SESSION_FILE = "last_session.json"


class AutoClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Auto Clicker Macro - Perekam & Pemutar Klik Background")
        self.geometry("920x720")
        self.minsize(800, 600)

        # Inisialisasi Engine
        self.engine = MacroEngine()
        self.engine.on_step_added = self._on_engine_step_added
        self.engine.on_playback_step = self._on_engine_playback_step
        self.engine.on_state_changed = self._on_engine_state_changed

        self.step_widgets = []
        self._active_highlight_idx = -1

        # Bangun Komponen UI
        self._build_header()
        self._build_action_bar()
        self._build_settings_bar()
        self._build_steps_container()
        self._build_footer()

        # Update window boundary untuk ignore clicks di UI saat merekam
        self.after(500, self._update_window_bounds_loop)

        # Muat sesi terakhir jika ada
        self._load_auto_session()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_header(self):
        """Header dengan info judul, status aktif, dan petunjuk Hotkey."""
        header_frame = ctk.CTkFrame(self, corner_radius=10)
        header_frame.pack(fill="x", padx=16, pady=(12, 6))

        # Baris atas: Judul dan Badge Status
        top_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_row.pack(fill="x", padx=14, pady=(10, 4))

        title_label = ctk.CTkLabel(
            top_row,
            text="🖱️ Auto Clicker Macro Pro",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left")

        # Badge status (Siap, Merekam, Play, dll)
        self.status_badge = ctk.CTkLabel(
            top_row,
            text="🟢 SIAP",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#1E3A2F",
            text_color="#4ECCA3",
            corner_radius=8,
            padx=12,
            pady=4
        )
        self.status_badge.pack(side="right")

        # Baris bawah: Cheat-sheet Global Hotkey
        hotkey_bar = ctk.CTkFrame(header_frame, fg_color=("gray85", "#1F232A"), corner_radius=6)
        hotkey_bar.pack(fill="x", padx=14, pady=(2, 10))

        hotkey_text = (
            "⌨️ Global Shortcut (Bisa ditekan dari background/aplikasi lain):  "
            "[F6] Rekam / Selesai  •  [F7] Putar / Jeda  •  [F8] Stop Darurat"
        )
        hk_label = ctk.CTkLabel(
            hotkey_bar,
            text=hotkey_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray20", "#B0B8C4")
        )
        hk_label.pack(pady=5)

    def _build_action_bar(self):
        """Baris tombol utama: Record, Play, Stop, Simpan, Buka, Hapus."""
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=16, pady=4)

        # Tombol Rekam (F6)
        self.btn_record = ctk.CTkButton(
            action_frame,
            text="⏺️ Rekam (F6)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            width=140,
            height=38,
            command=self._toggle_record
        )
        self.btn_record.pack(side="left", padx=(0, 8))

        # Tombol Putar (F7)
        self.btn_play = ctk.CTkButton(
            action_frame,
            text="▶️ Putar (F7)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            width=130,
            height=38,
            command=self._toggle_play
        )
        self.btn_play.pack(side="left", padx=(0, 8))

        # Tombol Stop (F8)
        self.btn_stop = ctk.CTkButton(
            action_frame,
            text="⏹️ Stop (F8)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#546E7A",
            hover_color="#37474F",
            width=110,
            height=38,
            command=self.engine.stop_all
        )
        self.btn_stop.pack(side="left", padx=(0, 14))

        # Tombol Simpan Script
        self.btn_save = ctk.CTkButton(
            action_frame,
            text="💾 Simpan Script",
            width=120,
            height=38,
            command=self._save_script_dialog
        )
        self.btn_save.pack(side="left", padx=(0, 8))

        # Tombol Buka Script
        self.btn_load = ctk.CTkButton(
            action_frame,
            text="📂 Buka Script",
            width=110,
            height=38,
            fg_color="#455A64",
            hover_color="#37474F",
            command=self._load_script_dialog
        )
        self.btn_load.pack(side="left", padx=(0, 8))

        # Tombol Reset
        self.btn_clear = ctk.CTkButton(
            action_frame,
            text="🗑️ Reset Semua",
            width=110,
            height=38,
            fg_color="#78909C",
            hover_color="#546E7A",
            command=self._clear_all_steps
        )
        self.btn_clear.pack(side="right")

    def _build_settings_bar(self):
        """Baris pengaturan pengulangan (looping) dan jeda waktu default."""
        settings_frame = ctk.CTkFrame(self, corner_radius=10)
        settings_frame.pack(fill="x", padx=16, pady=6)

        # Kolom 1: Pengulangan (Loop)
        lbl_loop = ctk.CTkLabel(settings_frame, text="Ulangi (Loop):", font=ctk.CTkFont(weight="bold"))
        lbl_loop.pack(side="left", padx=(14, 6), pady=8)

        self.loop_options = ["1 Kali", "2 Kali", "3 Kali", "5 Kali", "10 Kali", "Berulang Terus (Infinite)"]
        self.cb_loop = ctk.CTkComboBox(
            settings_frame,
            values=self.loop_options,
            width=170,
            command=self._on_loop_change
        )
        self.cb_loop.set("1 Kali")
        self.cb_loop.pack(side="left", padx=(0, 16), pady=8)

        # Kolom 2: Jeda antar loop
        lbl_loop_delay = ctk.CTkLabel(settings_frame, text="Jeda Antar Loop (dtk):")
        lbl_loop_delay.pack(side="left", padx=(0, 6), pady=8)

        self.entry_loop_delay = ctk.CTkEntry(settings_frame, width=60)
        self.entry_loop_delay.insert(0, "1.0")
        self.entry_loop_delay.pack(side="left", padx=(0, 20), pady=8)
        self.entry_loop_delay.bind("<FocusOut>", self._on_loop_delay_change)
        self.entry_loop_delay.bind("<Return>", self._on_loop_delay_change)

        # Checkbox: Minimize saat play
        self.var_minimize_on_play = tk.BooleanVar(value=False)
        self.chk_minimize = ctk.CTkCheckBox(
            settings_frame,
            text="Minimize otomatis saat Play",
            variable=self.var_minimize_on_play
        )
        self.chk_minimize.pack(side="right", padx=14, pady=8)

    def _build_steps_container(self):
        """Daftar tabel langkah (Step List) dengan header kolom."""
        outer_frame = ctk.CTkFrame(self, corner_radius=10)
        outer_frame.pack(fill="both", expand=True, padx=16, pady=6)

        # Header Kolom
        header_row = ctk.CTkFrame(outer_frame, height=32, fg_color=("gray80", "#242831"), corner_radius=6)
        header_row.pack(fill="x", padx=8, pady=(8, 4))

        col_step = ctk.CTkLabel(header_row, text="Step", width=55, font=ctk.CTkFont(weight="bold"))
        col_step.pack(side="left", padx=4)

        col_pos = ctk.CTkLabel(header_row, text="Posisi Layar (X, Y)", width=170, font=ctk.CTkFont(weight="bold"), anchor="w")
        col_pos.pack(side="left", padx=6)

        col_act = ctk.CTkLabel(header_row, text="Jenis Klik", width=140, font=ctk.CTkFont(weight="bold"), anchor="w")
        col_act.pack(side="left", padx=6)

        col_delay = ctk.CTkLabel(header_row, text="Jeda Sebelum Klik (detik)", width=190, font=ctk.CTkFont(weight="bold"), anchor="w")
        col_delay.pack(side="left", padx=6)

        col_ops = ctk.CTkLabel(header_row, text="Aksi", width=110, font=ctk.CTkFont(weight="bold"))
        col_ops.pack(side="right", padx=10)

        # Scrollable container untuk daftar baris step
        self.steps_scroll = ctk.CTkScrollableFrame(outer_frame, corner_radius=6)
        self.steps_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        # Baris toolbar di bawah tabel: Tambah Step Manual & Tangkap Posisi Kursor
        tbl_tools = ctk.CTkFrame(outer_frame, fg_color="transparent")
        tbl_tools.pack(fill="x", padx=8, pady=(2, 8))

        btn_capture = ctk.CTkButton(
            tbl_tools,
            text="📍 Ambil Posisi Kursor (3 dtk)",
            width=200,
            command=self._capture_cursor_countdown
        )
        btn_capture.pack(side="left", padx=(4, 8))

        btn_add_manual = ctk.CTkButton(
            tbl_tools,
            text="➕ Tambah Step Manual",
            width=170,
            fg_color="#37474F",
            command=self._add_manual_step
        )
        btn_add_manual.pack(side="left")

    def _build_footer(self):
        """Status bar bawah dengan jumlah step, total durasi estimasi, dan status teks."""
        footer_frame = ctk.CTkFrame(self, height=36, corner_radius=0, fg_color=("gray90", "#181A20"))
        footer_frame.pack(fill="x", side="bottom")

        self.lbl_status_msg = ctk.CTkLabel(
            footer_frame,
            text="Aplikasi siap. Klik 'Rekam (F6)' atau buka script yang sudah ada.",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_status_msg.pack(side="left", padx=16, pady=4)

        self.lbl_stats = ctk.CTkLabel(
            footer_frame,
            text="Total: 0 Langkah | Estimasi: 0.0 detik",
            anchor="e",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray30", "#A0AEC0")
        )
        self.lbl_stats.pack(side="right", padx=16, pady=4)

    # ------------------ MANAJEMEN UI STEP LIST ------------------
    def _refresh_all_steps_ui(self):
        """Render ulang semua baris step di dalam scrollable frame."""
        for widget in self.steps_scroll.winfo_children():
            widget.destroy()
        self.step_widgets.clear()

        for idx, step in enumerate(self.engine.steps):
            self._create_step_row(step, idx)

        self._update_stats()

    def _create_step_row(self, step: MacroStep, idx: int):
        """Membuat 1 baris widget untuk sebuah langkah."""
        row_frame = ctk.CTkFrame(self.steps_scroll, corner_radius=6, height=44)
        row_frame.pack(fill="x", pady=2, padx=2)

        # Label Nomor Step
        lbl_num = ctk.CTkLabel(row_frame, text=f"#{idx + 1}", width=50, font=ctk.CTkFont(weight="bold"))
        lbl_num.pack(side="left", padx=4)

        # Label Koordinat (X, Y)
        lbl_pos = ctk.CTkLabel(
            row_frame,
            text=f"X: {step.x}   Y: {step.y}",
            width=170,
            anchor="w",
            font=ctk.CTkFont(family="Consolas", size=13)
        )
        lbl_pos.pack(side="left", padx=6)

        # Dropdown Jenis Klik
        action_map = {
            "left": "Klik Kiri",
            "right": "Klik Kanan",
            "double": "Klik Ganda",
            "middle": "Klik Tengah"
        }
        reverse_action_map = {v: k for k, v in action_map.items()}

        cb_act = ctk.CTkComboBox(
            row_frame,
            values=["Klik Kiri", "Klik Kanan", "Klik Ganda", "Klik Tengah"],
            width=130,
            command=lambda val, s=step: self._on_step_action_change(s, reverse_action_map.get(val, "left"))
        )
        cb_act.set(action_map.get(step.action, "Klik Kiri"))
        cb_act.pack(side="left", padx=6)

        # Entry Jeda Waktu (Delay)
        delay_container = ctk.CTkFrame(row_frame, fg_color="transparent")
        delay_container.pack(side="left", padx=6)

        entry_delay = ctk.CTkEntry(delay_container, width=70)
        entry_delay.insert(0, str(step.delay))
        entry_delay.pack(side="left", padx=(0, 4))
        
        lbl_unit = ctk.CTkLabel(delay_container, text="detik", text_color="gray")
        lbl_unit.pack(side="left")

        def save_delay(event=None, s=step, ent=entry_delay):
            try:
                val = float(ent.get())
                s.delay = max(0.05, round(val, 2))
                ent.delete(0, "end")
                ent.insert(0, str(s.delay))
                self._update_stats()
            except ValueError:
                ent.delete(0, "end")
                ent.insert(0, str(s.delay))

        entry_delay.bind("<FocusOut>", save_delay)
        entry_delay.bind("<Return>", save_delay)

        # Tombol Aksi: Test & Hapus
        btn_del = ctk.CTkButton(
            row_frame,
            text="❌",
            width=36,
            height=30,
            fg_color="#C62828",
            hover_color="#8E0000",
            command=lambda i=idx: self._delete_step(i)
        )
        btn_del.pack(side="right", padx=(4, 8))

        btn_test = ctk.CTkButton(
            row_frame,
            text="🎯 Tes",
            width=60,
            height=30,
            fg_color="#00838F",
            hover_color="#006064",
            command=lambda i=idx: self.engine.test_single_step(i)
        )
        btn_test.pack(side="right", padx=4)

        self.step_widgets.append(row_frame)

    def _delete_step(self, idx: int):
        """Hapus langkah pada index dan refresh."""
        self.engine.remove_step(idx)
        self._refresh_all_steps_ui()

    def _update_stats(self):
        """Hitung total langkah dan estimasi total waktu per putaran."""
        total_steps = len(self.engine.steps)
        total_time = sum(step.delay for step in self.engine.steps)
        self.lbl_stats.configure(text=f"Total: {total_steps} Langkah | Estimasi: {total_time:.2f} detik / putaran")

    def _on_step_action_change(self, step: MacroStep, new_action: str):
        step.action = new_action

    def _on_loop_change(self, choice: str):
        if "Infinite" in choice:
            self.engine.loop_count = 0
        else:
            try:
                num = int(choice.split()[0])
                self.engine.loop_count = num
            except Exception:
                self.engine.loop_count = 1

    def _on_loop_delay_change(self, event=None):
        try:
            val = float(self.entry_loop_delay.get())
            self.engine.loop_delay = max(0.0, val)
        except ValueError:
            self.entry_loop_delay.delete(0, "end")
            self.entry_loop_delay.insert(0, str(self.engine.loop_delay))

    # ------------------ ENGINE CALLBACKS (THREAD-SAFE) ------------------
    def _on_engine_step_added(self, step: MacroStep, idx: int):
        """Dipanggil dari thread listener mouse saat ada klik baru."""
        self.after(0, lambda: self._add_single_step_ui(step, idx))

    def _add_single_step_ui(self, step: MacroStep, idx: int):
        self._create_step_row(step, idx)
        self._update_stats()
        # Scroll ke bawah otomatis
        try:
            self.steps_scroll._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _on_engine_playback_step(self, step_idx: int, loop_idx: int):
        """Dipanggil saat playback sedang menjalankan langkah tertentu."""
        self.after(0, lambda: self._highlight_step_row(step_idx, loop_idx))

    def _highlight_step_row(self, step_idx: int, loop_idx: int):
        # Reset highlight sebelumnya
        if 0 <= self._active_highlight_idx < len(self.step_widgets):
            prev_row = self.step_widgets[self._active_highlight_idx]
            prev_row.configure(fg_color=["#cfd8dc", "#2B2D30"])

        self._active_highlight_idx = step_idx

        # Pasang highlight baru
        if 0 <= step_idx < len(self.step_widgets):
            curr_row = self.step_widgets[step_idx]
            curr_row.configure(fg_color="#1565C0")  # Biru terang saat aktif
            self.lbl_status_msg.configure(
                text=f"▶️ Loop ke-{loop_idx}: Mengeksekusi Langkah #{step_idx + 1} dari {len(self.engine.steps)}..."
            )

    def _on_engine_state_changed(self, state: str, message: str):
        """Dipanggil saat status engine berubah (idle, recording, playing, paused)."""
        self.after(0, lambda: self._update_state_ui(state, message))

    def _update_state_ui(self, state: str, message: str):
        self.lbl_status_msg.configure(text=message)

        if state == "recording":
            self.status_badge.configure(text="🔴 MEREKAM...", fg_color="#4A1515", text_color="#FF6B6B")
            self.btn_record.configure(text="⏹️ Selesai (F6)", fg_color="#B71C1C")
            self.btn_play.configure(state="disabled")
        elif state == "playing":
            self.status_badge.configure(text="🔵 MEMUTAR...", fg_color="#0D3059", text_color="#64B5F6")
            self.btn_record.configure(state="disabled")
            self.btn_play.configure(text="⏸️ Jeda (F7)", fg_color="#F57C00")
            if self.var_minimize_on_play.get():
                self.iconify()
        elif state == "paused":
            self.status_badge.configure(text="🟡 DIJEDA", fg_color="#4E3B06", text_color="#FFD54F")
            self.btn_play.configure(text="▶️ Lanjut (F7)", fg_color="#2E7D32")
        else:  # idle
            self.status_badge.configure(text="🟢 SIAP", fg_color="#1E3A2F", text_color="#4ECCA3")
            self.btn_record.configure(state="normal", text="⏺️ Rekam (F6)", fg_color="#D32F2F")
            self.btn_play.configure(state="normal", text="▶️ Putar (F7)", fg_color="#2E7D32")
            if self.state() == "iconic":
                self.deiconify()

    # ------------------ AKSI TOMBOL UTAMA ------------------
    def _toggle_record(self):
        if self.engine.is_recording:
            self.engine.stop_recording()
        else:
            self.engine.start_recording(append=True)

    def _toggle_play(self):
        if self.engine.is_playing:
            self.engine.toggle_pause()
        else:
            if not self.engine.steps:
                messagebox.showwarning("Peringatan", "Belum ada langkah yang direkam! Klik 'Rekam (F6)' terlebih dahulu.")
                return
            self.engine.start_playback()

    def _clear_all_steps(self):
        if not self.engine.steps:
            return
        if messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin menghapus semua langkah?"):
            self.engine.clear_steps()
            self._refresh_all_steps_ui()
            self.lbl_status_msg.configure(text="Semua langkah berhasil dibersihkan.")

    def _add_manual_step(self):
        """Dialog untuk menambahkan step dengan koordinat manual."""
        cur_x, cur_y = get_current_cursor_pos()
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Tambah Step Manual")
        dialog.geometry("340x260")
        dialog.resizable(False, False)
        dialog.grab_set()

        lbl_coord = ctk.CTkLabel(dialog, text="Koordinat Mouse (Pixel):", font=ctk.CTkFont(weight="bold"))
        lbl_coord.pack(pady=(16, 4))

        frame_xy = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_xy.pack(pady=4)

        ctk.CTkLabel(frame_xy, text="X:").pack(side="left", padx=4)
        ent_x = ctk.CTkEntry(frame_xy, width=70)
        ent_x.insert(0, str(cur_x))
        ent_x.pack(side="left", padx=4)

        ctk.CTkLabel(frame_xy, text="Y:").pack(side="left", padx=4)
        ent_y = ctk.CTkEntry(frame_xy, width=70)
        ent_y.insert(0, str(cur_y))
        ent_y.pack(side="left", padx=4)

        lbl_act = ctk.CTkLabel(dialog, text="Jenis Klik & Jeda:", font=ctk.CTkFont(weight="bold"))
        lbl_act.pack(pady=(10, 4))

        frame_opt = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_opt.pack(pady=4)

        cb_action = ctk.CTkComboBox(frame_opt, values=["Klik Kiri", "Klik Kanan", "Klik Ganda"], width=130)
        cb_action.set("Klik Kiri")
        cb_action.pack(side="left", padx=4)

        ent_del = ctk.CTkEntry(frame_opt, width=60)
        ent_del.insert(0, "1.0")
        ent_del.pack(side="left", padx=4)
        ctk.CTkLabel(frame_opt, text="detik").pack(side="left")

        def submit():
            try:
                x = int(ent_x.get())
                y = int(ent_y.get())
                d = max(0.05, float(ent_del.get()))
                act_map = {"Klik Kiri": "left", "Klik Kanan": "right", "Klik Ganda": "double"}
                act = act_map.get(cb_action.get(), "left")
                self.engine.add_step(x, y, act, d)
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Input angka koordinat atau jeda tidak valid!")

        btn_ok = ctk.CTkButton(dialog, text="Tambahkan Langkah", command=submit)
        btn_ok.pack(pady=(16, 0))

    def _capture_cursor_countdown(self):
        """Countdown 3 detik lalu otomatis merekam posisi kursor saat ini."""
        def worker():
            for i in range(3, 0, -1):
                self.lbl_status_msg.configure(text=f"📍 Arahkan kursor ke target! Menangkap dalam {i} detik...")
                time.sleep(1)
            cx, cy = get_current_cursor_pos()
            self.lbl_status_msg.configure(text=f"✅ Posisi tertangkap: X={cx}, Y={cy}")
            self.engine.add_step(cx, cy, "left", 1.0)

        threading.Thread(target=worker, daemon=True).start()

    # ------------------ SIMPAN & MUAT SCRIPT ------------------
    def _save_script_dialog(self):
        """Buka dialog simpan file JSON."""
        if not self.engine.steps:
            messagebox.showinfo("Informasi", "Tidak ada langkah yang dapat disimpan.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Macro Files", "*.json"), ("Semua File", "*.*")],
            title="Simpan Script Makro"
        )
        if filepath:
            self.engine.save_to_file(filepath)
            self.lbl_status_msg.configure(text=f"Script berhasil disimpan ke: {os.path.basename(filepath)}")

    def _load_script_dialog(self):
        """Buka dialog muat file JSON."""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON Macro Files", "*.json"), ("Semua File", "*.*")],
            title="Buka Script Makro"
        )
        if filepath:
            try:
                self.engine.load_from_file(filepath)
                self._sync_settings_to_ui()
                self._refresh_all_steps_ui()
                self.lbl_status_msg.configure(text=f"Script berhasil dimuat: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Gagal Membuka", f"Format file tidak sesuai:\n{e}")

    def _sync_settings_to_ui(self):
        """Sinkronisasi pengaturan loop dari file ke widget GUI."""
        if self.engine.loop_count == 0:
            self.cb_loop.set("Berulang Terus (Infinite)")
        else:
            matching = [opt for opt in self.loop_options if opt.startswith(f"{self.engine.loop_count} ")]
            if matching:
                self.cb_loop.set(matching[0])
            else:
                self.cb_loop.set(f"{self.engine.loop_count} Kali")

        self.entry_loop_delay.delete(0, "end")
        self.entry_loop_delay.insert(0, str(self.engine.loop_delay))

    def _load_auto_session(self):
        """Muat otomatis sesi terakhir jika file last_session.json tersedia."""
        if os.path.exists(SESSION_FILE):
            try:
                self.engine.load_from_file(SESSION_FILE)
                self._sync_settings_to_ui()
                self._refresh_all_steps_ui()
                self.lbl_status_msg.configure(text=f"Sesi sebelumnya berhasil dimuat otomatis ({len(self.engine.steps)} langkah).")
            except Exception:
                pass

    def _save_auto_session(self):
        """Simpan otomatis ke last_session.json agar langkah tidak hilang besok."""
        try:
            self.engine.save_to_file(SESSION_FILE)
        except Exception:
            pass

    def _update_window_bounds_loop(self):
        """Mengupdate batas koordinat jendela agar klik pada jendela sendiri diabaikan saat merekam."""
        try:
            x = self.winfo_rootx()
            y = self.winfo_rooty()
            w = self.winfo_width()
            h = self.winfo_height()
            self.engine.set_window_bbox((x, y, x + w, y + h))
        except Exception:
            pass
        self.after(800, self._update_window_bounds_loop)

    def _on_close(self):
        """Handle penutupan aplikasi."""
        self.engine.stop_all()
        self._save_auto_session()
        self.destroy()


def main():
    app = AutoClickerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
