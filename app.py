import streamlit as st
import zipfile
import re
from lxml import etree
import io

st.set_page_config(page_title="KMZ Renamer Pro - ISP Tools", page_icon="🌐", layout="wide")

st.title("🌐 KMZ Advanced Renamer")
st.markdown("Alat khusus untuk penamaan massal homepass ISP.")

# Sidebar untuk Pengaturan Penamaan
st.sidebar.header("Konfigurasi Nama Baru")
prefix = st.sidebar.text_input("Awalan Nama (Prefix)", placeholder="Contoh: No. atau A-")
start_index = st.sidebar.number_input("Mulai Urutan Dari", min_value=0, value=1, step=1)
remove_old_no = st.sidebar.checkbox("Hapus teks 'No.' bawaan asli", value=True)

uploaded_file = st.file_uploader("Upload file KMZ (Maks 1GB)", type=["kmz"])

if uploaded_file is not None:
    with st.spinner('Sedang memproses ratusan titik...'):
        try:
            input_kmz = zipfile.ZipFile(uploaded_file, 'r')
            kml_filename = next((f for f in input_kmz.namelist() if f.endswith('.kml')), None)
            
            if not kml_filename:
                st.error("Format KMZ tidak valid (doc.kml tidak ditemukan).")
            else:
                kml_content = input_kmz.read(kml_filename)
                parser = etree.XMLParser(recover=True)
                tree = etree.fromstring(kml_content, parser=parser)
                
                # Menggunakan query yang lebih dalam untuk menjangkau semua Placemark
                # Mencari tag <name> yang merupakan anak dari <Placemark>
                placemarks = tree.xpath('//*[local-name()="Placemark"]')
                
                log_updates = []
                current_number = start_index
                
                for pm in placemarks:
                    # Cari tag <name> di dalam Placemark ini
                    name_element = pm.find('.//*[local-name()="name"]')
                    
                    if name_element is not None:
                        old_text = name_element.text if name_element.text else ""
                        
                        # Gabungkan Prefix + Urutan Angka
                        new_text = f"{prefix}{current_number}"
                        
                        name_element.text = new_text
                        log_updates.append(f"Titik {current_number}: '{old_text}' ➜ '{new_text}'")
                        
                        current_number += 1
                
                # Re-build KMZ
                new_kml_content = etree.tostring(tree, xml_declaration=True, encoding='UTF-8', pretty_print=True)
                
                output_kmz = io.BytesIO()
                with zipfile.ZipFile(output_kmz, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                    new_zip.writestr(kml_filename, new_kml_content)
                    for item in input_kmz.infolist():
                        if item.filename != kml_filename:
                            new_zip.writestr(item, input_kmz.read(item.filename))
                
                st.success(f"Berhasil memproses {len(placemarks)} titik homepass!")

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download KMZ Hasil Rename",
                        data=output_kmz.getvalue(),
                        file_name=f"Renamed_{uploaded_file.name}",
                        mime="application/vnd.google-earth.kmz"
                    )
                
                with col2:
                    with st.expander("Lihat Log Penamaan"):
                        for log in log_updates:
                            st.caption(log)

            input_kmz.close()

        except Exception as e:
            st.error(f"Terjadi error saat pemrosesan: {e}")
            st.info("Saran: Pastikan file KMZ tidak dalam keadaan rusak atau terbuka di Google Earth saat diupload.")