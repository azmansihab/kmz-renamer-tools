import streamlit as st
import zipfile
from lxml import etree
import io
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="ISP KMZ Renamer Pro",
    page_icon="📍",
    layout="wide"
)

# Custom CSS untuk mempercantik tampilan
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #007bff; color: white; border-radius: 8px; }
    .stFileInfo { background-color: #ffffff; border-radius: 10px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- JUDUL APLIKASI ---
st.title("📍 ISP KMZ Advanced Renamer")
st.write("Solusi profesional untuk penamaan massal titik homepass secara berurutan.")

# --- SIDEBAR: PENGATURAN PENAMAAN ---
st.sidebar.header("⚙️ Konfigurasi Nama")
prefix = st.sidebar.text_input("Awalan (Prefix)", value="", placeholder="Contoh: No. atau A-")
start_number = st.sidebar.number_input("Mulai Urutan Dari", min_value=0, value=1, step=1)
suffix = st.sidebar.text_input("Akhiran (Suffix)", value="", placeholder="Contoh: -JKT")

st.sidebar.markdown("---")
st.sidebar.info("""
**Instruksi:**
1. Atur format nama di atas.
2. Upload file KMZ Anda.
3. Aplikasi akan merename setiap titik (Placemark) secara otomatis.
4. Download hasil perbaikan.
""")

# --- AREA UPLOAD ---
uploaded_file = st.file_uploader("Upload File KMZ (Maksimal 1GB)", type=["kmz"])

if uploaded_file is not None:
    with st.status("Sedang memproses file besar...", expanded=True) as status:
        try:
            # 1. Membaca file KMZ
            input_kmz = zipfile.ZipFile(uploaded_file, 'r')
            
            # 2. Mencari file KML utama (biasanya doc.kml)
            kml_filename = next((f for f in input_kmz.namelist() if f.lower().endswith('.kml')), None)
            
            if not kml_filename:
                st.error("Error: Tidak ditemukan file KML di dalam KMZ ini.")
            else:
                st.write("🔍 Membedah struktur data...")
                kml_content = input_kmz.read(kml_filename)
                
                # 3. Parsing XML dengan lxml (Sangat stabil untuk 500+ titik)
                # recover=True digunakan jika ada karakter ilegal di dalam file asli
                parser = etree.XMLParser(recover=True, encoding='utf-8', remove_blank_text=True)
                tree = etree.fromstring(kml_content, parser=parser)
                
                # 4. Mencari semua elemen Placemark tanpa peduli Namespace
                placemarks = tree.xpath('//*[local-name()="Placemark"]')
                
                if not placemarks:
                    st.warning("Peringatan: Berhasil membaca file, tapi tidak ditemukan titik koordinat (Placemark).")
                else:
                    st.write(f"📝 Merename {len(placemarks)} titik...")
                    
                    log_updates = []
                    current_num = start_number
                    
                    for pm in placemarks:
                        # Cari atau buat tag <name> di dalam Placemark
                        name_tag = pm.find('.//*[local-name()="name"]')
                        if name_tag is None:
                            # Jika titik tidak punya nama, kita buatkan elemen <name> baru
                            name_tag = etree.SubElement(pm, "{http://www.opengis.net/kml/2.2}name")
                        
                        old_name = name_tag.text if name_tag.text else "N/A"
                        new_name = f"{prefix}{current_num}{suffix}"
                        
                        # Eksekusi Rename
                        name_tag.text = new_name
                        log_updates.append({"Asli": old_name, "Baru": new_name})
                        current_num += 1
                    
                    # 5. Membangun kembali file KML hasil edit
                    new_kml_data = etree.tostring(tree, xml_declaration=True, encoding='UTF-8', pretty_print=True)
                    
                    # 6. Membungkus kembali ke paket KMZ (Memory-efficient)
                    output_buffer = io.BytesIO()
                    with zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as new_kmz:
                        # Masukkan KML yang sudah diupdate
                        new_kmz.writestr(kml_filename, new_kml_data)
                        
                        # Salin file pendukung (seperti foto/media yang ada di file Anda)
                        for item in input_kmz.infolist():
                            if item.filename != kml_filename:
                                try:
                                    new_kmz.writestr(item, input_kmz.read(item.filename))
                                except:
                                    continue # Lewati jika ada file media yang rusak
                    
                    status.update(label="✅ Proses Selesai!", state="complete", expanded=False)
                    
                    # --- DOWNLOAD & LOG ---
                    st.success(f"Berhasil memproses {len(placemarks)} titik!")
                    
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.download_button(
                            label="📥 Download KMZ Hasil Rename",
                            data=output_buffer.getvalue(),
                            file_name=f"Renamed_{uploaded_file.name}",
                            mime="application/vnd.google-earth.kmz"
                        )
                    
                    with col2:
                        with st.expander("Lihat Log Perubahan Nama"):
                            st.table(log_updates[:100])
                            if len(log_updates) > 100:
                                st.write(f"...dan {len(log_updates)-100} titik lainnya.")

            input_kmz.close()

        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {str(e)}")
            st.info("Saran: Pastikan file KMZ tidak rusak dan coba lagi.")