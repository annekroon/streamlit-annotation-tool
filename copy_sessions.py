import os
import shutil

# Always work relative to the script's own directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# Configuration for syncing final samples
CONFIG = {
    "local_dir": "sessions_final",
    "annotation_file": "annotations_final.csv",
    "webdav_dir": "/home/akroon/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/annotations/coding_frames/final_sample/sessions"
}

def sync_sessions(config):
    local_dir = config["local_dir"]
    annotation_file = config["annotation_file"]
    webdav_dir = config["webdav_dir"]

    print(f"\n🔄 Start synchronisatie voor 'final sample'")
    os.makedirs(webdav_dir, exist_ok=True)

    try:
        files = os.listdir(local_dir)
    except FileNotFoundError:
        print(f"❌ Map '{local_dir}' niet gevonden.")
        return

    # Copy all .json files in the local directory
    session_files = [f for f in files if f.lower().endswith(".json")]
    if not session_files:
        print("⚠️ Geen sessiebestanden gevonden om te synchroniseren.")
        return

    for filename in session_files:
        local_path = os.path.join(local_dir, filename)
        webdav_path = os.path.join(webdav_dir, filename)
        try:
            shutil.copy2(local_path, webdav_path)
            print(f"✅ {filename} succesvol gekopieerd naar WebDAV.")
        except Exception as e:
            print(f"❌ Fout bij kopiëren van {filename}: {e}")

    # Copy the annotation file, if present
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
