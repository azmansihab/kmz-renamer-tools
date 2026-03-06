import streamlit as st
import zipfile
import re
from lxml import etree
import io

# Konfigurasi Halaman Streamlit
st.set_page_config(page_title="ISP KMZ Renamer Pro", page_icon="📍", layout="wide")

# Tambahkan CSS untuk tampilan yang lebih profesional
st.markdown("""
    <style>
    .stAlert { margin-top: 20px; }
    .stDownloadButton button { width: 100%; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("📍 ISP KMZ Advanced Renamer")
st.write("Gunakan alat ini untuk merename massal homepass (titik) pada file KMZ secara berurutan.")

# --- SIDEBAR KONFIGURASI ---
st.sidebar.header("⚙️ Pengaturan Nama Baru")
prefix = st.sidebar.text_input("Awalan (Prefix)", value="", placeholder="Contoh: No. atau A-")
start_num = st.sidebar.number_input("Mulai dari Angka", min_value=0, value=1, step=1)
suffix = st.sidebar.text_input("Akhiran (Suffix)", value="", placeholder="Contoh: -JKT")

st.sidebar.markdown("---")
st.sidebar.info("Aplikasi ini akan mencari setiap **Placemark** (titik) dan mengganti label namanya secara berurutan sesuai pengaturan di atas.")

# --- AREA UPLOAD ---
uploaded_file = st.file_uploader("Upload file KMZ Anda (Maksimal 1GB)", type=["kmz"])

if uploaded_file is not None:
    with st.spinner('Sedang memproses file...'):
        try:
            # 1. Membaca file KMZ
            input_kmz = zipfile.ZipFile(uploaded_file, 'r')
            
            # 2. Cari file KML (bisa doc.kml atau nama lain)
            kml_filename = next((f for f in input_kmz.namelist() if f.lower().endswith('.kml')), None)
            
            if not kml_filename:
                st.error("Error: Tidak ditemukan file KML di dalam KMZ ini.")
            else:
                kml_content = input_kmz.read(kml_filename)
                
                # 3. Parsing XML dengan mode 'Recover' agar tidak gampang error jika ada karakter aneh
                parser = etree.XMLParser(recover=True, remove_blank_text=True)
                tree = etree.fromstring(kml_content, parser=parser)
                
                # 4. Cari SEMUA elemen Placemark menggunakan XPath (Namespace Agnostic)
                # Ini adalah bagian kunci agar tidak terjadi error "0 titik diubah"
                placemarks = tree.xpath('//*[local-name()="Placemark"]')
                
                if not placemarks:
                    st.warning("Peringatan: Berhasil membaca file, tapi tidak ditemukan objek 'Placemark' di dalamnya.")
                else:
                    log_updates = []
                    current_count = start_num
                    
                    for pm in placemarks:
                        # Cari tag <name> di dalam Placemark
                        name_tag = pm.find('.//*[local-name()="name"]')
                        
                        # Jika tag <name> tidak ada (titik tanpa nama), kita buatkan baru
                        if name_tag is None:
                            # Gunakan default namespace KML jika memungkinkan
                            name_tag = etree.SubElement(pm, "{http://www.opengis.net/kml/2.2}name")
                        
                        old_text = name_tag.text if name_tag.text else "N/A"
                        new_text = f"{prefix}{current_count}{suffix}"
                        
                        # Proses Rename
                        name_tag.text = new_text
                        log_updates.append({"Asli": old_text, "Baru": new_text})
                        current_count += 1
                    
                    # 5. Bangun kembali KML ke format String
                    new_kml_data = etree.tostring(tree, xml_declaration=True, encoding='UTF-8', pretty_print=True)
                    
                    # 6. Bungkus ke KMZ baru (di memori/RAM)
                    output_buffer = io.BytesIO()
                    with zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as new_kmz:
                        # Masukkan KML yang sudah diupdate
                        new_kmz.writestr(kml_filename, new_kml_data)
                        
                        # Salin file lain (gambar, icon, dll) agar tidak hilang
                        for item in input_kmz.infolist():
                            if item.filename != kml_filename:
                                new_kmz.writestr(item, input_kmz.read(item.filename))
                    
                    st.success(f"✅ Berhasil merename {len(placemarks)} titik homepass!")
                    
                    # Tombol Download & Log
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.download_button(
                            label="📥 Download Hasil Rename",
                            data=output_buffer.getvalue(),
                            file_name=f"Renamed_{uploaded_file.name}",
                            mime="application/vnd.google-earth.kmz"
                        )
                    
                    with col2:
                        with st.expander("Lihat Detail Hasil Rename (Maks 100 data)"):
                            st.table(log_updates[:100])

            input_kmz.close()

        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {str(e)}")
            st.info("Saran: Coba bersihkan file KMZ Anda di Google Earth Pro sebelum diupload kembali.")