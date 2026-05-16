"""
Google Colab Setup Script
=========================
Run this in Google Colab to train the Rickets model on free GPU (T4/A100)

Steps:
1. Upload your Dataset/Rickets folder to Google Drive
2. Run all cells in Google Colab
3. Download the trained model (rickets_best.pth)
"""

# ============================================================================
# CELL 1: Mount Google Drive and Install Dependencies
# ============================================================================
# Run this cell first
"""
from google.colab import drive
import os

# Mount Drive
drive.mount('/content/drive')

# Navigate to project
os.chdir('/content/drive/MyDrive/medical-ai/backend')  # Adjust path as needed

# Install requirements
!pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
!pip install -q fastapi uvicorn python-multipart Pillow numpy scikit-learn opencv-python-headless httpx pydantic matplotlib python-dotenv scipy tqdm
"""

# ============================================================================
# CELL 2: Check GPU and Dataset
# ============================================================================
"""
import torch
print(f"GPU Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU Name: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# Check dataset
import os
train_path = './data/rickets/train'
if os.path.exists(train_path):
    for cls in os.listdir(train_path):
        cls_path = os.path.join(train_path, cls)
        count = len(os.listdir(cls_path))
        print(f"{cls}: {count} images")
else:
    print("Dataset not found. Make sure to prepare the data first.")
"""

# ============================================================================
# CELL 3: Prepare Data (if not already done)
# ============================================================================
"""
# Run prepare_data.py to organize the Rickets dataset
os.chdir('/content/drive/MyDrive/medical-ai')
!python backend/prepare_data.py --dataset rickets \\
    --src Dataset/Rickets \\
    --dst backend/data \\
    --val_split 0.2
"""

# ============================================================================
# CELL 4: Download models.py files (if needed)
# ============================================================================
"""
# Ensure model files exist
# You may need to manually copy them to Colab or create them there
import os
os.chdir('/content/drive/MyDrive/medical-ai/backend')
"""

# ============================================================================
# CELL 5: Train Rickets Model with GPU
# ============================================================================
"""
import os
os.chdir('/content/drive/MyDrive/medical-ai/backend')

# Run training with GPU acceleration
!python train_rickets_cloud.py \\
    --data_dir ./data/rickets \\
    --save_dir ./checkpoints \\
    --epochs 100 \\
    --batch_size 32 \\
    --use_gpu
"""

# ============================================================================
# CELL 6: Download Results
# ============================================================================
"""
# After training completes, download the model and history
from google.colab import files
import os

os.chdir('/content/drive/MyDrive/medical-ai/backend/checkpoints')

print("Files ready for download:")
for f in os.listdir('.'):
    print(f"  - {f}")

# Download all checkpoint files
files.download('rickets_best.pth')
files.download('rickets_history.json')
files.download('rickets_curves.png')
"""
