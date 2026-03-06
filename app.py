import streamlit as st
import zipfile
import re
from lxml import etree
import io

# Konfigurasi Halaman
st.set_page_config(page_title="KMZ Renamer Pro", page_icon="🌐", layout="wide")

# CSS Custom agar tampilan lebih rapi
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007BFF;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌐 KMZ Advanced Renamer for ISP")
st.write("Alat bantu untuk merename ribuan homepass secara otomatis berdasarkan urutan.")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Pengaturan Penamaan")
prefix = st.sidebar.text_input("Awalan (Prefix)", value="", placeholder="Contoh: No. atau Blok-")
start_number = st.sidebar.number_input("Mulai dari Angka", min_value=0, value=1, step=1)
suffix = st.sidebar.text_input("Akhiran (Suffix)", value="", placeholder="Contoh: -JKT")

st.sidebar.markdown("---")
st.sidebar.info("""
**Cara Kerja:**
1. Upload file KMZ.
2. Atur Prefix dan Angka Mulai.
3. Klik Download.
Aplikasi akan mencari setiap **Placemark** dan mengganti namanya sesuai urutan.
""")

# --- MAIN INTERFACE ---
uploaded_file = st.file_uploader("Upload file KMZ Anda (Maks 1GB)", type=["kmz"])

if uploaded_file is not None:
    with st.spinner('Memproses data... Mohon tunggu sebentar.'):
        try:
            # Membaca KMZ asli
            input_kmz = zipfile.ZipFile(uploaded_file, 'r')
            
            # Mencari file KML di dalam KMZ secara dinamis
            kml_filename = next((f for f in input_kmz.namelist() if f.endswith('.kml')), None)
            
            if not kml_filename:
                st.error("File KML tidak ditemukan di dalam paket KMZ.")
            else:
                # Membaca isi KML
                kml_content = input_kmz.read(kml_filename)
                
                # Parsing dengan lxml (lebih stabil untuk file besar)
                parser = etree.XMLParser(recover=True, remove_blank_text=True)
                tree = etree.fromstring(kml_content, parser=parser)
                
                # Mencari semua elemen Placemark (titik/garis/poligon)
                # Menggunakan wildcard namespace agar tidak error di berbagai versi KML
                placemarks = tree.xpath('//*[local-name()="Placemark"]')
                
                log_data = []
                current_num = start_number
                
                for pm in placemarks:
                    # Cari tag <name> di dalam Placemark tersebut
                    name_tag = pm.find('.//*[local-name()="name"]')
                    
                    # Jika tag <name> tidak ada, kita buatkan baru agar tetap ter-rename
                    if name_tag is None:
                        name_tag = etree.SubElement(pm, "{http://www.opengis.net/kml/2.2}name")
                    
                    old_val = name_tag.text if name_tag.text else "Tanpa Nama"
                    new_val = f"{prefix}{current_num}{suffix}"
                    
                    name_tag.text = new_val
                    log_data.append({"Asli": old_val, "Baru": new_val})
                    current_num += 1
                
                # Konversi kembali ke String XML
                new_kml_str = etree.tostring(tree, xml_declaration=True, encoding='UTF-8', pretty_print=True)
                
                # Membuat file KMZ baru di memori
                output_buffer = io.BytesIO()
                with zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as new_kmz:
                    # Tulis KML yang sudah dimodifikasi
                    new_kmz.writestr(kml_filename, new_kml_str)
                    
                    # Copy semua file pendukung (images, icons) agar file tidak rusak
                    for item in input_kmz.infolist():
                        if item.filename != kml_filename:
                            new_kmz.writestr(item, input_kmz.read(item.filename))
                
                st.success(f"✅ Berhasil memproses {len(placemarks)} titik!")
                
                # Layout Tombol Download & Log
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.download_button(
                        label="📥 Unduh KMZ Hasil Rename",
                        data=output_buffer.getvalue(),
                        file_name=f"Renamed_{uploaded_file.name}",
                        mime="application/vnd.google-earth.kmz"
                    )
                
                with col2:
                    with st.expander("Lihat Detail Perubahan"):
                        st.table(log_data[:100]) # Tampilkan 100 pertama agar tidak berat
                        if len(log_data) > 100:
                            st.write(f"...dan {len(log_data)-100} titik lainnya.")

            input_kmz.close()

        except Exception as e:
            st.error(f"Terjadi Kesalahan: {str(e)}")