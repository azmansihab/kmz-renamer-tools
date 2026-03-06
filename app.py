import streamlit as st
import zipfile
from lxml import etree
import io

# 1. Konfigurasi Halaman
st.set_page_config(page_title="ISP KMZ Renamer Pro", page_icon="📍", layout="wide")

st.title("📍 ISP KMZ Advanced Renamer")
st.info("Sistem ini dioptimalkan untuk file KMZ besar (ISP/Homepass) yang berisi banyak foto.")

# 2. Sidebar Konfigurasi
st.sidebar.header("⚙️ Pengaturan Nama")
prefix = st.sidebar.text_input("Awalan (Prefix)", value="", placeholder="Contoh: No. atau A-")
start_number = st.sidebar.number_input("Mulai dari Angka", min_value=0, value=1, step=1)
suffix = st.sidebar.text_input("Akhiran (Suffix)", value="", placeholder="Contoh: -JKT")

# 3. Area Upload
uploaded_file = st.file_uploader("Upload file KMZ Anda", type=["kmz"])

if uploaded_file is not None:
    with st.spinner('Sedang memproses... Harap jangan menutup browser.'):
        try:
            # Membaca file ke RAM
            input_zip_bytes = uploaded_file.read()
            input_kmz = zipfile.ZipFile(io.BytesIO(input_zip_bytes), 'r')
            
            # Cari file KML utama (doc.kml atau lainnya)
            kml_filename = next((f for f in input_kmz.namelist() if f.lower().endswith('.kml')), None)
            
            if not kml_filename:
                st.error("File KML tidak ditemukan di dalam paket KMZ.")
            else:
                # Parsing XML dengan mode Recover (Anti-Error)
                kml_content = input_kmz.read(kml_filename)
                parser = etree.XMLParser(recover=True, encoding='utf-8')
                tree = etree.fromstring(kml_content, parser=parser)
                
                # Cari semua elemen Placemark (Titik)
                placemarks = tree.xpath('//*[local-name()="Placemark"]')
                
                if not placemarks:
                    st.warning("Berhasil membaca file, tapi tidak ditemukan titik Placemark.")
                else:
                    log_updates = []
                    current_num = start_number
                    
                    for pm in placemarks:
                        # Cari atau buat tag <name>
                        name_tag = pm.find('.//*[local-name()="name"]')
                        if name_tag is None:
                            name_tag = etree.SubElement(pm, "{http://www.opengis.net/kml/2.2}name")
                        
                        old_name = name_tag.text if name_tag.text else "N/A"
                        new_name = f"{prefix}{current_num}{suffix}"
                        
                        name_tag.text = new_name
                        log_updates.append({"Asli": old_name, "Baru": new_name})
                        current_num += 1
                    
                    # Build KML String
                    new_kml_bytes = etree.tostring(tree, xml_declaration=True, encoding='UTF-8', pretty_print=True)
                    
                    # Simpan ke KMZ baru (Proteksi Zip64 untuk file banyak foto)
                    output_buffer = io.BytesIO()
                    with zipfile.ZipFile(output_buffer, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as new_kmz:
                        new_kmz.writestr(kml_filename, new_kml_bytes)
                        
                        # Salin file media/foto asli agar tidak hilang
                        for item in input_kmz.infolist():
                            if item.filename != kml_filename:
                                try:
                                    new_kmz.writestr(item, input_kmz.read(item.filename))
                                except:
                                    continue 
                    
                    st.success(f"✅ Berhasil merename {len(placemarks)} titik!")
                    
                    # Tombol Download
                    st.download_button(
                        label="📥 Download KMZ (Hasil Rename)",
                        data=output_buffer.getvalue(),
                        file_name=f"Renamed_{uploaded_file.name}",
                        mime="application/vnd.google-earth.kmz"
                    )
                    
                    with st.expander("Lihat Rincian Perubahan"):
                        st.table(log_updates[:100])

            input_kmz.close()
        except Exception as e:
            st.error(f"Terjadi Error: {str(e)}")