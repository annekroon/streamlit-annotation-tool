import os
import shutil

# Lokale sessiemap
LOCAL_SESSIONS_DIR = "sessions"

# WebDAV-doelmap (pas dit aan naar jouw juiste pad)
WEBDAV_SESSIONS_DIR = "/home/akroon/webdav/ASCOR-FMG-5580-RESPOND-news-data (Projectfolder)/sessions"

def sync_sessions():
    os.makedirs(WEBDAV_SESSIONS_DIR, exist_ok=True)

    files = os.listdir(LOCAL_SESSIONS_DIR)
    for filename in files:
        local_path = os.path.join(LOCAL_SESSIONS_DIR, filename)
        webdav_path = os.path.join(WEBDAV_SESSIONS_DIR, filename)

        try:
            shutil.copy2(local_path, webdav_path)
            print(f"✅ {filename} succesvol gekopieerd naar WebDAV.")
        except Exception as e:
            print(f"❌ Fout bij kopiëren van {filename}: {e}")

if __name__ == "__main__":
    sync_sessions()
