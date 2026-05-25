# app_auto.py
# Aplikasi Desktop + Auto Scan Multi Film & Multi Wilayah
# (REFACTORED SESUAI LOGIC test5.py)

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import csv
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class XXIAutoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("XXI Auto Scanner - Multi Film & Wilayah")
        self.geometry("1400x800")
        
        # =========================================================
        # VARIABLES
        # =========================================================
        self.is_scanning = False
        self.scan_thread = None
        self.driver = None
        self.wait = None
        self.data_results = []
        self.row_counter = 0
        
        # Default config
        self.films = [
            {"id": "16TPRK", "name": "TUMBAL PROYEK"},
        ]
        self.regions = ["Bekasi", "Jakarta", "Tangerang", "Depok", "Bogor"]
        
        self.create_widgets()
        self.after(500, self.check_chrome)
    
    # =========================================================
    # UI FUNCTIONS
    # =========================================================
    
    def create_widgets(self):
        """Buat seluruh UI"""
        
        # ========== FRAME KIRI (CONTROL PANEL) ==========
        left_frame = ctk.CTkFrame(self, width=350)
        left_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        # Header
        ctk.CTkLabel(left_frame, text="XXI Auto Scanner", font=("Arial", 22, "bold")).pack(pady=15)
        ctk.CTkLabel(left_frame, text="Multi Film & Multi Wilayah", font=("Arial", 12)).pack(pady=(0, 20))
        
        ctk.CTkFrame(left_frame, height=2, fg_color="gray").pack(fill="x", padx=10, pady=5)
        
        # Chrome Status
        self.chrome_status = ctk.CTkLabel(left_frame, text="🌐 Chrome: Belum terkoneksi", font=("Arial", 12), text_color="orange")
        self.chrome_status.pack(pady=5)
        
        ctk.CTkButton(left_frame, text="🔌 Konek Chrome", command=self.connect_chrome, height=35).pack(fill="x", padx=15, pady=5)
        
        ctk.CTkFrame(left_frame, height=2, fg_color="gray").pack(fill="x", padx=10, pady=10)
        
        # ===== KONFIGURASI =====
        ctk.CTkLabel(left_frame, text="📋 KONFIGURASI SCAN", font=("Arial", 14, "bold")).pack(anchor="w", padx=15)
        
        # Film
        ctk.CTkLabel(left_frame, text="Film (ID - Nama):", font=("Arial", 11, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        self.film_listbox = ctk.CTkTextbox(left_frame, height=70, font=("Courier", 10))
        self.film_listbox.pack(fill="x", padx=15, pady=5)
        self.film_listbox.insert("1.0", "16TPRK - TUMBAL PROYEK\n")
        
        add_film_frame = ctk.CTkFrame(left_frame)
        add_film_frame.pack(fill="x", padx=15, pady=2)
        ctk.CTkButton(add_film_frame, text="+ Tambah Film", command=self.add_film, height=30, fg_color="gray", width=100).pack(side="left", padx=2)
        ctk.CTkButton(add_film_frame, text="🗑️ Clear", command=self.clear_films, height=30, fg_color="red", width=100).pack(side="left", padx=2)
        
        # Wilayah
        ctk.CTkLabel(left_frame, text="Wilayah (satu per baris):", font=("Arial", 11, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        self.region_listbox = ctk.CTkTextbox(left_frame, height=70, font=("Courier", 10))
        self.region_listbox.pack(fill="x", padx=15, pady=5)
        self.region_listbox.insert("1.0", "Bekasi\nJakarta\nTangerang\nDepok\nBogor")
        
        add_region_frame = ctk.CTkFrame(left_frame)
        add_region_frame.pack(fill="x", padx=15, pady=2)
        ctk.CTkButton(add_region_frame, text="+ Tambah Wilayah", command=self.add_region, height=30, fg_color="gray", width=120).pack(side="left", padx=2)
        ctk.CTkButton(add_region_frame, text="🗑️ Clear", command=self.clear_regions, height=30, fg_color="red", width=100).pack(side="left", padx=2)
        
        ctk.CTkFrame(left_frame, height=2, fg_color="gray").pack(fill="x", padx=10, pady=10)
        
        # ===== CONTROL BUTTONS =====
        self.scan_btn = ctk.CTkButton(left_frame, text="🚀 MULAI SCAN", command=self.start_scan, height=50, font=("Arial", 14, "bold"), fg_color="green")
        self.scan_btn.pack(fill="x", padx=15, pady=5)
        
        self.stop_btn = ctk.CTkButton(left_frame, text="⏹️ STOP SCAN", command=self.stop_scan, height=40, fg_color="red", state="disabled")
        self.stop_btn.pack(fill="x", padx=15, pady=5)
        
        self.export_btn = ctk.CTkButton(left_frame, text="💾 EXPORT CSV", command=self.export_csv, height=40, fg_color="blue", state="disabled")
        self.export_btn.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkButton(left_frame, text="🗑️ CLEAR DATA", command=self.clear_results, height=40, fg_color="orange").pack(fill="x", padx=15, pady=5)
        
        ctk.CTkFrame(left_frame, height=2, fg_color="gray").pack(fill="x", padx=10, pady=10)
        
        # ===== PROGRESS =====
        self.progress = ctk.CTkProgressBar(left_frame, height=20)
        self.progress.pack(fill="x", padx=15, pady=5)
        self.progress.set(0)
        
        self.progress_label = ctk.CTkLabel(left_frame, text="0% (0/0)", font=("Arial", 12, "bold"))
        self.progress_label.pack()
        
        self.status_label = ctk.CTkLabel(left_frame, text="⚡ Status: Siap", font=("Arial", 11), text_color="cyan")
        self.status_label.pack(pady=10)
        
        # ========== FRAME KANAN (HASIL + LOG) ==========
        right_frame = ctk.CTkFrame(self)
        right_frame.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)
        
        # Header Tabel
        header_frame = ctk.CTkFrame(right_frame)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="📊 HASIL SCAN REAL-TIME", font=("Arial", 16, "bold")).pack(side="left", padx=10)
        self.total_label = ctk.CTkLabel(header_frame, text="Total: 0 sesi", font=("Arial", 12), text_color="cyan")
        self.total_label.pack(side="right", padx=10)
        
        # Tabel Hasil
        table_frame = ctk.CTkFrame(right_frame)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        columns = ("No", "Film", "Wilayah", "Bioskop", "Jam", "Kosong", "Terisi", "Waktu")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        col_widths = [35, 140, 110, 220, 70, 70, 70, 120]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")
        
        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Log
        log_frame = ctk.CTkFrame(right_frame)
        log_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(log_frame, text="📝 LOG ACTIVITY", font=("Arial", 12, "bold")).pack(anchor="w", padx=5)
        self.log_text = ctk.CTkTextbox(log_frame, height=120, font=("Consolas", 9))
        self.log_text.pack(fill="x", padx=5, pady=5)
    
    # =========================================================
    # CHROME CONNECTION
    # =========================================================
    
    def check_chrome(self):
        """Cek apakah Chrome sudah konek"""
        try:
            options = webdriver.ChromeOptions()
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            test = webdriver.Chrome(options=options)
            test.quit()
            self.chrome_status.configure(text="🌐 Chrome: Terkoneksi", text_color="green")
            return True
        except:
            self.chrome_status.configure(text="🌐 Chrome: Tidak terhubung", text_color="red")
            return False
    
    def connect_chrome(self):
        """Connect ke Chrome dengan debug port"""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            
            options = webdriver.ChromeOptions()
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 15)
            
            self.add_log("✅ Berhasil terkoneksi ke Chrome")
            self.chrome_status.configure(text="🌐 Chrome: Terkoneksi", text_color="green")
            return True
        except Exception as e:
            self.add_log(f"❌ Gagal konek Chrome: {str(e)[:60]}")
            self.chrome_status.configure(text="🌐 Chrome: Gagal", text_color="red")
            messagebox.showerror("Error", f"Tidak bisa konek ke Chrome!\n\nError: {str(e)}")
            return False
    
    # =========================================================
    # UI UTILITIES
    # =========================================================
    
    def add_log(self, msg):
        """Tambah log ke text widget"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {msg}\n")
        self.log_text.see("end")
        self.update_idletasks()
    
    def add_film(self):
        """Dialog tambah film"""
        dialog = ctk.CTkInputDialog(text="Masukkan ID Film (misal: 16TPRK):", title="Tambah Film")
        film_id = dialog.get_input()
        if film_id:
            dialog2 = ctk.CTkInputDialog(text="Masukkan Nama Film:", title="Tambah Film")
            film_name = dialog2.get_input()
            if film_name:
                self.film_listbox.insert("end", f"{film_id.strip()} - {film_name.strip()}\n")
                self.add_log(f"✅ Film ditambahkan: {film_name}")
    
    def clear_films(self):
        """Clear daftar film"""
        self.film_listbox.delete("1.0", "end")
        self.add_log("🗑️ Daftar film dikosongkan")
    
    def add_region(self):
        """Dialog tambah wilayah"""
        dialog = ctk.CTkInputDialog(text="Masukkan nama wilayah:", title="Tambah Wilayah")
        region = dialog.get_input()
        if region:
            self.region_listbox.insert("end", f"{region.strip()}\n")
            self.add_log(f"✅ Wilayah ditambahkan: {region}")
    
    def clear_regions(self):
        """Clear daftar wilayah"""
        self.region_listbox.delete("1.0", "end")
        self.add_log("🗑️ Daftar wilayah dikosongkan")
    
    def clear_results(self):
        """Clear hasil scan"""
        self.tree.delete(*self.tree.get_children())
        self.data_results = []
        self.row_counter = 0
        self.total_label.configure(text="Total: 0 sesi")
        self.add_log("🗑️ Data hasil scan dikosongkan")
    
    # =========================================================
    # CONFIG PARSER
    # =========================================================
    
    def get_films(self):
        """Parse daftar film dari textbox"""
        films = []
        text = self.film_listbox.get("1.0", "end-1c")
        for line in text.split("\n"):
            if line.strip():
                parts = line.split(" - ")
                if len(parts) == 2:
                    films.append({
                        "id": parts[0].strip(),
                        "name": parts[1].strip()
                    })
        return films
    
    def get_regions(self):
        """Parse daftar wilayah dari textbox"""
        regions = []
        text = self.region_listbox.get("1.0", "end-1c")
        for line in text.split("\n"):
            if line.strip():
                regions.append(line.strip())
        return regions
    
    # =========================================================
    # SELENIUM HELPERS (DARI test5.py)
    # =========================================================
    
    def wait_ready(self, timeout=10):
        """Tunggu sampai DOM ready"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(1.5)
        except:
            pass
    
    def click_real(self, el):
        """Click element dengan JavaScript"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.3)
            self.driver.execute_script("""
                const el = arguments[0];
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles:true}));
                el.dispatchEvent(new MouseEvent('mouseup', {bubbles:true}));
                el.dispatchEvent(new MouseEvent('click', {bubbles:true}));
            """, el)
            return True
        except Exception as e:
            return False
    
    def handle_error_popup(self):
        """Handle error popup (masih dalam perbaikan)"""
        try:
            popups = self.driver.find_elements(By.XPATH, "//*[contains(text(),'masih dalam perbaikan')]")
            if len(popups) == 0:
                return False
            
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                try:
                    txt = btn.text.strip().lower()
                    if txt == "siap":
                        self.click_real(btn)
                        time.sleep(2)
                        return True
                except:
                    pass
        except:
            pass
        return False
    
    def handle_quantity_popup(self):
        """Handle quantity popup"""
        for _ in range(10):
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    try:
                        if not btn.is_displayed():
                            continue
                        txt = btn.text.strip().lower()
                        if "continue" in txt:
                            self.click_real(btn)
                            time.sleep(2)
                            return True
                    except:
                        pass
            except:
                pass
            time.sleep(1)
        return False
    
    def wait_for_seatmap(self, max_wait=20):
        """Tunggu seatmap muncul"""
        for i in range(max_wait):
            current = self.driver.current_url.lower()
            if "booking_ref" not in current:
                time.sleep(1)
                continue
            try:
                children = self.driver.find_elements(By.CSS_SELECTOR, "[class*='seats__list'] *")
                if len(children) > 50:
                    time.sleep(2)
                    return True
            except:
                pass
            time.sleep(1)
        return False
    
    def count_seats(self):
        """Hitung kursi kosong & terisi"""
        js = """
        const items = document.querySelectorAll("[class*='TheaterSeats_cell']");
        let kosong = 0; let isi = 0;
        items.forEach(el => {
            const cls = el.className.toLowerCase();
            const txt = el.textContent.trim();
            if (txt === "" && !cls.includes('free') && !cls.includes('sold') && !cls.includes('available') && !cls.includes('booked')) {
                return;
            }
            if (cls.includes('free') || cls.includes('available') || cls.includes('active')) {
                kosong++; return;
            }
            if (cls.includes('sold') || cls.includes('booked') || cls.includes('disabled') || cls.includes('reserved')) {
                isi++; return;
            }
            const style = window.getComputedStyle(el);
            if (style.opacity === "0.5" || style.opacity === "0.3" || style.pointerEvents === "none") {
                isi++;
            } else {
                kosong++;
            }
        });
        return { kosong, isi, total: kosong + isi };
        """
        result = self.driver.execute_script(js)
        return result
    
    def get_active_cinemas(self):
        """Ambil daftar bioskop aktif"""
        cinema_names = []
        try:
            cinema_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'XXI') or contains(text(), 'IMAX') or contains(text(), 'Premiere')]")
            for elem in cinema_elements:
                try:
                    name = elem.text.strip()
                    if name and len(name) > 3 and name not in cinema_names:
                        if name.lower() not in ["bekasi", "jakarta", "tangerang", "depok", "bogor", "schedule", "movies", "cinemas"]:
                            cinema_names.append(name)
                except:
                    continue
        except:
            pass
        return cinema_names
    
    def get_showtimes(self):
        """Ambil daftar jam tayang"""
        list_jam_aktif = []
        time.sleep(1)
        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            kandidat_elemen = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'time')] | //p | //button | //a")
            
            for el in kandidat_elemen:
                try:
                    teks = el.text.strip()
                    if len(teks) == 5 and (":" in teks or "." in teks):
                        if el.is_displayed():
                            if teks not in list_jam_aktif:
                                list_jam_aktif.append(teks)
                except:
                    continue
        except:
            pass
        return list_jam_aktif
    
    def go_back(self, film_url, region, cinema_name):
        """Kembali ke halaman schedule"""
        try:
            self.driver.get(film_url)
            self.wait_ready()
            
            link_region = self.wait.until(
                EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{region}')] | //*[text()='{region}']"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_region)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", link_region)
            time.sleep(2)
            
            cinema_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{cinema_name}')]"))
            )
            self.click_real(cinema_btn)
            self.wait_ready()
        except Exception as e:
            pass
    
    # =========================================================
    # MAIN SCAN LOGIC
    # =========================================================
    
    def start_scan(self):
        """Mulai scan"""
        if self.is_scanning:
            messagebox.showwarning("Peringatan", "Scan sedang berjalan!")
            return
        
        if not self.driver:
            if not self.connect_chrome():
                return
        
        films = self.get_films()
        regions = self.get_regions()
        
        if not films or not regions:
            messagebox.showerror("Error", "Isi daftar film dan wilayah terlebih dahulu!")
            return
        
        self.is_scanning = True
        self.scan_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.export_btn.configure(state="disabled")
        self.data_results = []
        self.row_counter = 0
        self.tree.delete(*self.tree.get_children())
        self.progress.set(0)
        self.total_label.configure(text="Total: 0 sesi")
        
        self.add_log(f"🚀 SCAN DIMULAI - {len(films)} film, {len(regions)} wilayah")
        
        self.scan_thread = threading.Thread(target=self.scan_loop, args=(films, regions), daemon=True)
        self.scan_thread.start()
    
    def stop_scan(self):
        """Stop scan"""
        self.is_scanning = False
        self.add_log("⏹️ Scan dihentikan manual")
        self.status_label.configure(text="⚡ Status: Dihentikan")
    
    def scan_loop(self, films, regions):
        """Main scan loop (SESUAI test5.py)"""
        total_combinations = len(films) * len(regions)
        current = 0
        
        try:
            for film in films:
                if not self.is_scanning:
                    break
                
                film_url = f"https://m.21cineplex.com/id/movies/{film['id']}"
                film_name = film['name']
                
                self.add_log(f"\n{'='*60}")
                self.add_log(f"🎬 MEMPROSES FILM: {film_name}")
                self.add_log(f"{'='*60}")
                self.status_label.configure(text=f"⚡ Status: Memproses film {film_name}")
                
                for region in regions:
                    if not self.is_scanning:
                        break
                    
                    current += 1
                    pct = int(current / total_combinations * 100)
                    self.progress.set(current / total_combinations)
                    self.progress_label.configure(text=f"{pct}% ({current}/{total_combinations})")
                    
                    self.add_log(f"\n{'#'*60}")
                    self.add_log(f"📍 WILAYAH: {region}")
                    self.add_log(f"{'#'*60}")
                    self.status_label.configure(text=f"⚡ Status: {film_name} - {region}")
                    
                    try:
                        # Buka halaman film
                        self.driver.get(film_url)
                        self.wait_ready(timeout=10)
                        
                        # Klik wilayah
                        try:
                            region_btn = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{region}')]")
                            self.driver.execute_script("arguments[0].click(); arguments[0].click();", region_btn)
                            time.sleep(3)
                        except Exception as e:
                            self.add_log(f"⚠️ Gagal klik wilayah {region}: {str(e)[:40]}")
                            continue
                        
                        # Dapatkan daftar bioskop
                        daftar_bioskop = self.get_active_cinemas()
                        self.add_log(f"✅ Ditemukan {len(daftar_bioskop)} bioskop: {daftar_bioskop}")
                        
                        if len(daftar_bioskop) == 0:
                            self.add_log(f"⚠️ Tidak ada bioskop di {region}")
                            continue
                        
                        # Proses setiap bioskop
                        for nama_bioskop in daftar_bioskop:
                            if not self.is_scanning:
                                break
                            
                            self.add_log(f"\n   🎬 BIOSKOP: {nama_bioskop}")
                            self.status_label.configure(text=f"⚡ Status: {nama_bioskop}")
                            
                            try:
                                # Reset halaman
                                self.driver.get(film_url)
                                self.wait_ready(timeout=10)
                                
                                # Klik wilayah
                                try:
                                    region_btn = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{region}')]")
                                    self.driver.execute_script("arguments[0].click(); arguments[0].click();", region_btn)
                                    time.sleep(3)
                                except:
                                    self.add_log(f"   ⚠️ Gagal klik wilayah")
                                    continue
                                
                                # Klik bioskop
                                try:
                                    target = self.wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{nama_bioskop}')]")))
                                    self.driver.execute_script("""
                                        var el = arguments[0];
                                        el.scrollIntoView({block: 'center'});
                                        el.dispatchEvent(new MouseEvent('mousedown', {bubbles:true}));
                                        el.dispatchEvent(new MouseEvent('mouseup', {bubbles:true}));
                                        el.dispatchEvent(new MouseEvent('click', {bubbles:true}));
                                    """, target)
                                    time.sleep(2)
                                except Exception as e:
                                    self.add_log(f"   ⚠️ Gagal klik bioskop: {str(e)[:40]}")
                                    continue
                                
                                # Dapatkan jam tayang
                                showtimes = self.get_showtimes()
                                self.add_log(f"   ✅ Jam tayang: {len(showtimes)} sesi -> {showtimes}")
                                
                                if len(showtimes) == 0:
                                    self.add_log(f"   ⚠️ Tidak ada jam tayang")
                                    continue
                                
                                # Loop setiap jam
                                for idx, showtime in enumerate(showtimes):
                                    if not self.is_scanning:
                                        break
                                    
                                    self.add_log(f"      [{idx+1}/{len(showtimes)}] Jam: {showtime}...")
                                    
                                    try:
                                        # Reset & buka kembali bioskop
                                        self.driver.get(film_url)
                                        self.wait_ready()
                                        
                                        region_btn = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{region}')]")
                                        self.driver.execute_script("arguments[0].click(); arguments[0].click();", region_btn)
                                        time.sleep(3)
                                        
                                        target = self.wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{nama_bioskop}')]")))
                                        self.click_real(target)
                                        time.sleep(2)
                                        
                                        # Klik jam tayang
                                        time_buttons = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{showtime}')] | //*[text()='{showtime}']")
                                        target_btn = None
                                        for btn in time_buttons:
                                            try:
                                                if btn.is_displayed():
                                                    target_btn = btn
                                                    break
                                            except:
                                                pass
                                        
                                        if target_btn is None:
                                            self.add_log(f"      ⚠️ Jam {showtime} tidak ditemukan")
                                            continue
                                        
                                        self.click_real(target_btn)
                                        time.sleep(2)
                                        
                                        # Handle popup error
                                        if self.handle_error_popup():
                                            self.add_log(f"      ⚠️ Showtime invalid (error popup)")
                                            continue
                                        
                                        # Handle quantity popup
                                        if not self.handle_quantity_popup():
                                            self.add_log(f"      ⚠️ Popup continue gagal")
                                            continue
                                        
                                        # Tunggu seatmap
                                        if not self.wait_for_seatmap():
                                            self.add_log(f"      ⚠️ Seatmap gagal dimuat")
                                            continue
                                        
                                        # Hitung kursi
                                        result = self.count_seats()
                                        
                                        if result['total'] > 0:
                                            self.row_counter += 1
                                            timestamp = datetime.now().strftime("%H:%M:%S")
                                            
                                            row_data = (
                                                self.row_counter,
                                                film_name,
                                                region,
                                                nama_bioskop,
                                                showtime,
                                                result['kosong'],
                                                result['isi'],
                                                timestamp
                                            )
                                            
                                            self.tree.insert("", 0, values=row_data)
                                            self.data_results.append(row_data)
                                            self.total_label.configure(text=f"Total: {len(self.data_results)} sesi")
                                            
                                            self.add_log(f"      ✅ Kosong={result['kosong']}, Terisi={result['isi']}, Total={result['total']}")
                                        else:
                                            self.add_log(f"      ⚠️ Total kursi = 0")
                                        
                                    except Exception as e:
                                        self.add_log(f"      ❌ Error: {str(e)[:50]}")
                                        continue
                            
                            except Exception as e:
                                self.add_log(f"   ❌ Bioskop error: {str(e)[:50]}")
                                continue
                    
                    except Exception as e:
                        self.add_log(f"❌ Wilayah error: {str(e)[:50]}")
                        continue
            
            self.add_log(f"\n{'='*60}")
            self.add_log(f"✅ SCAN SELESAI! Total: {len(self.data_results)} sesi")
            self.add_log(f"{'='*60}")
            self.status_label.configure(text="⚡ Status: SELESAI ✅")
        
        except Exception as e:
            self.add_log(f"❌ FATAL ERROR: {str(e)}")
            self.status_label.configure(text="⚡ Status: ERROR")
        
        finally:
            self.is_scanning = False
            self.scan_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.export_btn.configure(state="normal" if self.data_results else "disabled")
    
    # =========================================================
    # EXPORT
    # =========================================================
    
    def export_csv(self):
        """Export hasil ke CSV"""
        if not self.data_results:
            messagebox.showwarning("Peringatan", "Tidak ada data untuk di-export!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"xxi_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["No", "Film", "Wilayah", "Bioskop", "Jam", "Kosong", "Terisi", "Waktu"])
                    writer.writerows(self.data_results)
                
                messagebox.showinfo("Sukses", f"Data berhasil di-export!\n\n{filename}")
                self.add_log(f"💾 CSV Export: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal export:\n{str(e)}")

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    app = XXIAutoApp()
    app.mainloop()
