import streamlit as st
import zipfile
from lxml import etree
import io

# --- CONFIG ---
st.set_page_config(page_title="KMZ Renamer Ultra-Fast", layout="wide")
st.title("📍 ISP KMZ Renamer (High-Stability Version)")
st.write("Versi ini dioptimalkan untuk file dengan banyak foto (Media-Heavy KMZ).")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Konfigurasi Nama")
prefix = st.sidebar.text_input("Awalan (Prefix)", value="")
start_num = st.sidebar.number_input("Mulai dari Angka", min_value=0, value=1, step=1)
suffix = st.sidebar.text_input("Akhiran (Suffix)", value="")

# --- PROCESSING ---
uploaded_file = st.file_uploader("Upload file KMZ Anda", type=["kmz"])

if uploaded_file is not None:
    with st.spinner('Memproses KML... Media foto akan disalin otomatis.'):
        try:
            # Buka KMZ dari memori
            input_kmz = zipfile.ZipFile(uploaded_file, 'r')
            
            # Cari file KML utama
            kml_filename = next((f for f in input_kmz.namelist() if f.lower().endswith('.kml')), None)
            
            if not kml_filename:
                st.error("Gagal: File KML tidak ditemukan.")
            else:
                # 1. PROSES KML SAJA
                kml_data = input_kmz.read(kml_filename)
                parser = etree.XMLParser(recover=True, encoding='utf-8')
                tree = etree.fromstring(kml_data, parser=parser)
                
                placemarks = tree.xpath('//*[local-name()="Placemark"]')
                
                log_updates = []
                current_idx = start_num
                
                for pm in placemarks:
                    name_tag = pm.find('.//*[local-name()="name"]')
                    if name_tag is None:
                        name_tag = etree.SubElement(pm, "{http://www.opengis.net/kml/2.2}name")
                    
                    old_n = name_tag.text if name_tag.text else "N/A"
                    new_n = f"{prefix}{current_idx}{suffix}"
                    name_tag.text = new_n
                    log_updates.append({"Lama": old_n, "Baru": new_n})
                    current_idx += 1

                # 2. BUAT KMZ BARU DENGAN CARA MENYALIN FILE LAIN
                new_kml_bytes = etree.tostring(tree, xml_declaration=True, encoding='UTF-8')
                
                out_buffer = io.BytesIO()
                with zipfile.ZipFile(out_buffer, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as out_kmz:
                    # Masukkan KML baru
                    out_kmz.writestr(kml_filename, new_kml_bytes)
                    
                    # Salin file lain (media/foto) TANPA memprosesnya (Langsung Copy)
                    for item in input_kmz.infolist():
                        if item.filename != kml_filename:
                            try:
                                # Copy raw bytes untuk menghemat RAM
                                out_kmz.writestr(item.filename, input_kmz.read(item.filename))
                            except:
                                continue 

                st.success(f"Berhasil merename {len(placemarks)} titik!")
                st.download_button(
                    label="📥 Download Hasil Rename",
                    data=out_buffer.getvalue(),
                    file_name=f"Renamed_{uploaded_file.name}",
                    mime="application/vnd.google-earth.kmz"
                )
                
                with st.expander("Lihat Log (50 Data Pertama)"):
                    st.table(log_updates[:50])

            input_kmz.close()
        except Exception as e:
            st.error(f"Sistem Error: {str(e)}")
            st.info("Tips: Jika file Anda sangat besar, coba jalankan di GitHub Codespaces.")