import os
# Ignore the duplicate OpenMP library warning on Mac
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
from faster_whisper import WhisperModel

def cache_models():
    print("🚀 Starting model caching process...")

    print("\n🧠 1/2: Downloading and compiling Faster-Whisper 'base'...")
    # This downloads the weights to ~/.cache/huggingface and compiles the CTranslate2 binaries
    WhisperModel("base", device="cpu", compute_type="default")
    print("✅ Faster-Whisper cached successfully!")

    print("\n🧠 2/2: Downloading Silero VAD from GitHub...")
    # This downloads the repo to ~/.cache/torch/hub and bypasses the security prompt
    torch.hub.load(
        repo_or_dir='snakers4/silero-vad', 
        model='silero_vad', 
        force_reload=True, # Force a clean download
        trust_repo=True
    )
    print("✅ Silero VAD cached successfully!")

    print("\n🎉 All ML models are securely cached to your hard drive. You can now start FastAPI!")

if __name__ == "__main__":
    cache_models()