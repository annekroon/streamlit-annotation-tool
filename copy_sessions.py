import os
import shutil

# Always work relative to the script's own directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# Corrected configuration for syncing final samples
CONFIG = {
    "local_dir": "sessions_final",  # <-- corrected here
    "annotation_file": "annotations_final.csv",
    "webdav_dir": "/home/akroon/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/annotations/coding_frames/final_sample/sessions"
}

def is_final_sample(filename):
    # Customize this filter as needed — or remove if everything in sessions_final is valid
    return "final" in filename.lower()

def sync_sessions(config):
    local_dir = config["local_dir"]
    annotation_file = config["annotation_file"]
    webdav_dir = config["webdav_dir"]

    print(f"\n🔄 Start synchronisatie voor 'final sample'")

    os.makedirs(webdav_dir, exist_ok=True)

    # Copy final session files
    try:
        files = os.listdir(local_dir)
    except FileNotFoundError:
        print(f"❌ Map '{local_dir}' niet gevonden.")
        return

    final_files = [f for f in files if is_final_sample(f)]
    if not final_files:
        print("⚠️ Geen 'final' samples gevonden om te synchroniseren.")
        return

    for filename in final_files:
        local_path = os.path.join(local_dir, filename)
        webdav_path = os.path.join(webdav_dir, filename)

        try:
            shutil.copy2(local_path, webdav_path)
            print(f"✅ {filename} succesvol gekopieerd naar WebDAV.")
        except Exception as e:
            print(f"❌ Fout bij kopiëren van {filename}: {e}")

    # Copy annotation file
    if os.path.exists(annotation_file):
        try:
            destination = os.path.join(webdav_dir, annotation_file)
            shutil.copy2(annotation_file, destination)
            print(f"✅ {annotation_file} succesvol gekopieerd naar WebDAV.")
        except Exception as e:
            print(f"❌ Fout bij kopiëren van {annotation_file}: {e}")
    else:
        print(f"⚠️ {annotation_file} niet gevonden. Geen annotaties gekopieerd.")

if __name__ == "__main__":
    sync_sessions(CONFIG)
