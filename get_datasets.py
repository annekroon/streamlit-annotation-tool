import shutil
import os

# Lijst met extra CSV-bestanden
csv_files = [
    "/home/akroon/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/output/data-deductive-analysis/sample-manual-content-analysis/Bulgaria_Alexander_sample_250_llm_annotated.csv",
    "/home/akroon/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/output/data-deductive-analysis/sample-manual-content-analysis/Italy_Luigia_sample_250_llm_annotated.csv",
    "/home/akroon/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/output/data-deductive-analysis/sample-manual-content-analysis/Netherlands_Assia_sample_250_llm_annotated.csv",
    "/home/akroon/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/output/data-deductive-analysis/sample-manual-content-analysis/United_Kingdom_Elisa_sample_250_llm_annotated.csv"
]

# ICR sample 2
source_file = os.path.expanduser("~/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/annotations/coding_frames/ICR/ICR_test2/icr2_sample_LLM_annotated.csv")

# Doelmap
destination_dir = "/home/akroon/streamlit-annotation-tool/data"
os.makedirs(destination_dir, exist_ok=True)

# Functie om bestand te kopiëren
def copy_file(file_path):
    filename = os.path.basename(file_path)
    destination_file = os.path.join(destination_dir, filename)
    try:
        shutil.copy2(file_path, destination_file)
        print(f"✅ Bestand succesvol gekopieerd naar: {destination_file}")
    except Exception as e:
        print(f"❌ Fout bij kopiëren van {file_path}: {e}")

# Kopieer hoofdbronbestand
copy_file(source_file)

# Kopieer overige csv-bestanden
for csv_file in csv_files:
    copy_file(csv_file)
