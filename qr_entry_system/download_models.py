import requests
import os

# URLs for models (using a reliable CDN or GitHub Raw)
BASE_URL = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights"
LIB_URL = "https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js"

MODELS = [
    "ssd_mobilenetv1_model-weights_manifest.json",
    "ssd_mobilenetv1_model-shard1",
    "ssd_mobilenetv1_model-shard2",
    "face_landmark_68_model-weights_manifest.json",
    "face_landmark_68_model-shard1",
    "face_recognition_model-weights_manifest.json",
    "face_recognition_model-shard1",
    "face_recognition_model-shard2"
]

STATIC_JS_DIR = os.path.join("static", "js")
STATIC_MODELS_DIR = os.path.join("static", "models")

os.makedirs(STATIC_JS_DIR, exist_ok=True)
os.makedirs(STATIC_MODELS_DIR, exist_ok=True)

def download_file(url, folder, filename):
    print(f"Downloading {filename}...")
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(os.path.join(folder, filename), 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Done.")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")

# Download Library
download_file(LIB_URL, STATIC_JS_DIR, "face-api.min.js")

# Download Models
for model in MODELS:
    download_file(f"{BASE_URL}/{model}", STATIC_MODELS_DIR, model)

print("All downloads finished.")
