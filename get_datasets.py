import shutil
import os

# Pad naar bronbestand
source_file = os.path.expanduser("~/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/annotations/coding_frames/ICR/ICR_test2/icr2_sample_LLM_annotated.csv")

# Pad naar doelmap
destination_dir = "/home/akroon/streamlit-annotation-tool/data"

# Zorg dat de doelmap bestaat
os.makedirs(destination_dir, exist_ok=True)

# Houd originele bestandsnaam
filename = os.path.basename(source_file)
destination_file = os.path.join(destination_dir, filename)

# Kopieer bestand
try:
    shutil.copy2(source_file, destination_file)
    print(f"✅ Bestand succesvol gekopieerd naar: {destination_file}")
except Exception as e:
    print(f"❌ Fout bij kopiëren: {e}")
