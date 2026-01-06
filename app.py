import streamlit as st
import zipfile
import os
import tempfile
import xml.etree.ElementTree as ET

# Konfigurasi Halaman Web
st.set_page_config(page_title="KMZ Renamer Tool", layout="centered")

st.title("📍 KMZ Point Renamer")
st.markdown("""
**Tools untuk mengubah nama titik KMZ secara otomatis.**
Format output: **?-1, ?-2, ?-3, dst.** (Sesuai urutan).
*Note: Foto dan Deskripsi Popup AMAN (Tidak hilang).*
""")

def rename_kmz_points(input_kmz_path, output_kmz_path):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Ekstrak KMZ
            with zipfile.ZipFile(input_kmz_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Cari file doc.kml
            kml_path = os.path.join(temp_dir, "doc.kml")
            if not os.path.exists(kml_path):
                for root, dirs, files in os.walk(temp_dir):
                    if "doc.kml" in files:
                        kml_path = os.path.join(root, "doc.kml")
                        break
            
            if not os.path.exists(kml_path):
                return False, "File doc.kml tidak ditemukan."

            # 2. Parsing XML KML
            ET.register_namespace('', "http://www.opengis.net/kml/2.2")
            tree = ET.parse(kml_path)
            root = tree.getroot()
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}

            # 3. Rename Points
            counter = 1
            placemarks = root.findall('.//kml:Placemark', ns)
            
            if not placemarks:
                return False, "Tidak ditemukan Placemark (Titik) dalam file ini."

            for placemark in placemarks:
                name_tag = placemark.find('kml:name', ns)
                new_name = f"?-{counter}"
                
                if name_tag is not None:
                    name_tag.text = new_name
                else:
                    new_name_elem = ET.Element("name")
                    new_name_elem.text = new_name
                    placemark.insert(0, new_name_elem)
                
                counter += 1

            # 4. Simpan kembali doc.kml
            tree.write(kml_path, encoding='UTF-8', xml_declaration=True)

            # 5. Zip kembali
            with zipfile.ZipFile(output_kmz_path, 'w', zipfile.ZIP_DEFLATED) as kmz_out:
                for foldername, subfolders, filenames in os.walk(temp_dir):
                    for filename in filenames:
                        file_path = os.path.join(foldername, filename)
                        arcname = os.path.relpath(file_path, temp_dir)
                        kmz_out.write(file_path, arcname)
                        
        return True, "Sukses"
    except Exception as e:
        return False, str(e)

# --- UI Bagian Upload ---
uploaded_file = st.file_uploader("1. Upload File KMZ Anda", type="kmz")

if uploaded_file is not None:
    # Tampilkan info file
    st.info(f"File terdeteksi: {uploaded_file.name}")
    
    # Tombol Proses
    if st.button("2. Proses Rename Sekarang"):
        # Simpan sementara
        with tempfile.NamedTemporaryFile(delete=False, suffix=".kmz") as tmp_input:
            tmp_input.write(uploaded_file.getvalue())
            tmp_input_path = tmp_input.name

        output_filename = f"RENAMED_{uploaded_file.name}"
        tmp_output_path = os.path.join(tempfile.gettempdir(), output_filename)

        with st.spinner("Sedang memproses..."):
            success, msg = rename_kmz_points(tmp_input_path, tmp_output_path)
        
        if success:
            st.success(f"Berhasil! Total titik diproses.")
            with open(tmp_output_path, "rb") as f:
                st.download_button(
                    label="3. Download KMZ Baru",
                    data=f,
                    file_name=output_filename,
                    mime="application/vnd.google-earth.kmz",
                    type="primary"
                )
        else:
            st.error(f"Gagal: {msg}")
