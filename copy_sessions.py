import os
import shutil

# Always work relative to the script's own directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# Configuration options for both sync tasks
CONFIGS = {
    "default": {
        "local_dir": "sessions",
        "annotation_file": "annotations.csv",
        "webdav_dir": "/home/akroon/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/sessions"
    },
    "icr2": {
        "local_dir": "sessions_icr2",
        "annotation_file": "annotations_icr2.csv",
        "webdav_dir": "/home/akroon/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/annotations/coding_frames/ICR/ICR_test2/sessions"
    }
}

def sync_sessions(name, config):
    local_dir = config["local_dir"]
    annotation_file = config["annotation_file"]
    webdav_dir = config["webdav_dir"]

    print(f"\n🔄 Start synchronisatie voor '{name}'")

    os.makedirs(webdav_dir, exist_ok=True)

    # Copy session files
    try:
        files = os.listdir(local_dir)
    except FileNotFoundError:
        print(f"❌ Map '{local_dir}' niet gevonden.")
        return

    for filename in files:
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
    for name, config in CONFIGS.items():
        sync_sessions(name, config)
