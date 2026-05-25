def get_showtimes(self):
    """Ambil daftar jam tayang - DENGAN DEBUG"""
    list_jam_aktif = []
    time.sleep(2)
    try:
        # DUMP HTML untuk debug
        html_body = self.driver.page_source
        
        # Cari semua teks yang terlihat
        body_elem = self.driver.find_element(By.TAG_NAME, "body")
        body_text = body_elem.text
        
        # Debug: Save ke file
        with open("debug_showtimes.html", "w", encoding="utf-8") as f:
            f.write(html_body)
        with open("debug_showtimes.txt", "w", encoding="utf-8") as f:
            f.write(body_text)
        
        self.add_log("   📄 DEBUG: HTML & text disimpan ke debug_showtimes.*")
        
        # Method 1: Cari semua button & element dengan text mirip jam
        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
        self.add_log(f"   🔍 Found {len(all_buttons)} buttons")
        
        for btn in all_buttons:
            try:
                teks = btn.text.strip()
                if len(teks) >= 4 and len(teks) <= 6:
                    if ":" in teks or "." in teks:
                        parts = teks.replace(".", ":").split(":")
                        if len(parts) == 2:
                            try:
                                h = int(parts[0])
                                m = int(parts[1])
                                if 0 <= h <= 23 and 0 <= m <= 59:
                                    clean_time = f"{parts[0]}:{parts[1]}"
                                    if clean_time not in list_jam_aktif:
                                        list_jam_aktif.append(clean_time)
                                        self.add_log(f"   ✅ Found: {clean_time}")
                            except:
                                pass
            except:
                continue
        
        # Method 2: Cari dari semua span
        all_spans = self.driver.find_elements(By.TAG_NAME, "span")
        self.add_log(f"   🔍 Found {len(all_spans)} spans")
        
        for span in all_spans:
            try:
                teks = span.text.strip()
                if len(teks) == 5 and (":" in teks or "." in teks):
                    parts = teks.replace(".", ":").split(":")
                    if len(parts) == 2:
                        try:
                            h = int(parts[0])
                            m = int(parts[1])
                            if 0 <= h <= 23 and 0 <= m <= 59:
                                clean_time = f"{parts[0]}:{parts[1]}"
                                if clean_time not in list_jam_aktif:
                                    list_jam_aktif.append(clean_time)
                                    self.add_log(f"   ✅ Found: {clean_time}")
                        except:
                            pass
            except:
                continue
        
        # Method 3: Regex dari body text
        if len(list_jam_aktif) == 0:
            self.add_log("   ⚠️ Button/Span kosong, coba body text...")
            import re
            pattern = r'\b(\d{2})[:.(\s]*(\d{2})\b'
            matches = re.findall(pattern, body_text)
            
            for h, m in matches:
                try:
                    h_int = int(h)
                    m_int = int(m)
                    if 0 <= h_int <= 23 and 0 <= m_int <= 59:
                        clean_time = f"{h}:{m}"
                        if clean_time not in list_jam_aktif:
                            list_jam_aktif.append(clean_time)
                            self.add_log(f"   ✅ Found (regex): {clean_time}")
                except:
                    pass
        
        # Remove duplicates & sort
        list_jam_aktif = sorted(list(set(list_jam_aktif)))
        
        if len(list_jam_aktif) == 0:
            self.add_log("   ⚠️ TIDAK ADA JAM DITEMUKAN - Pakai default")
            list_jam_aktif = ["10:00", "13:00", "16:00", "19:00", "22:00"]
        
        self.add_log(f"   📊 Total jam ditemukan: {len(list_jam_aktif)}")
        return list_jam_aktif
    
    except Exception as e:
        self.add_log(f"   ❌ Error get_showtimes: {str(e)}")
        return ["10:00", "13:00", "16:00", "19:00", "22:00"]
