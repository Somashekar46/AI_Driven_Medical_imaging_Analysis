# Cloud GPU Training Guide - Medical AI Project

## Overview
This guide shows how to train the **Rickets Detection Model** using cloud GPU services for better accuracy and faster training.

---

## Option 1: Google Colab (FREE - Recommended for Quick Testing)

### Pros:
- ✅ **Free GPU** (T4 or sometimes A100)
- ✅ **No setup required** (runs in browser)
- ✅ **12 hours runtime** per session
- ✅ **Good for ~100 epochs**

### Steps:

1. **Prepare your dataset on Google Drive:**
   - Upload your `medical-ai` folder to Google Drive
   - Make sure `Dataset/Rickets` has all images

2. **Open Google Colab:**
   - Go to [colab.research.google.com](https://colab.research.google.com)
   - Create new notebook
   - Copy cells from `COLAB_SETUP.py`

3. **Run cells in order:**
   ```
   Cell 1: Mount Drive + Install Dependencies
   Cell 2: Check GPU & Dataset
   Cell 3: Prepare Data (if needed)
   Cell 4: Verify model files
   Cell 5: Train Model with GPU
   Cell 6: Download Results
   ```

4. **Training will complete in ~2-3 hours** for 100 epochs with batch size 32

5. **Download model files:**
   - `rickets_best.pth` - trained model
   - `rickets_history.json` - training metrics
   - `rickets_curves.png` - performance curves

---

## Option 2: AWS SageMaker (PAID but Flexible)

### Pros:
- ✅ Larger datasets
- ✅ More powerful GPUs (V100, A100)
- ✅ Production-ready
- ✅ Can train for unlimited time
- ⚠️ Costs vary ($0.50-$5.00/hour depending on GPU)

### Steps:

1. **Create AWS Account** and open SageMaker

2. **Upload dataset to S3:**
   ```bash
   aws s3 cp Dataset/Rickets s3://your-bucket/rickets --recursive
   ```

3. **Create Notebook Instance:**
   - Instance type: `ml.p3.2xlarge` (V100 GPU)
   - Root volume: 100 GB EBS

4. **In terminal, run:**
   ```bash
   cd /home/ec2-user/SageMaker
   git clone <your-repo>
   cd medical-ai/backend
   pip install -r requirements.txt
   
   # Download data from S3
   aws s3 cp s3://your-bucket/rickets ./data/rickets --recursive
   
   # Train
   python train_rickets_cloud.py \
     --data_dir ./data/rickets \
     --save_dir ./checkpoints \
     --epochs 100 \
     --batch_size 32 \
     --use_gpu
   ```

5. **Upload results back to S3:**
   ```bash
   aws s3 cp ./checkpoints s3://your-bucket/rickets-checkpoints --recursive
   ```

---

## Option 3: Azure ML (PAID but Easy Integration)

### Pros:
- ✅ Integrated with VS Code
- ✅ Easy experiment tracking
- ✅ Multiple GPU options
- ⚠️ Similar pricing to AWS

### Steps:

1. **Create Azure Account** and Azure ML workspace

2. **Install Azure CLI:**
   ```bash
   pip install azure-cli azure-ml
   az login
   ```

3. **Create training script** (already done: `train_rickets_cloud.py`)

4. **Submit training job:**
   ```bash
   az ml run submit-script \
     --resource-group your-rg \
     --workspace-name your-workspace \
     --experiment-name rickets-training \
     --conda-file requirements.txt \
     --compute-target gpu-cluster \
     --script-path train_rickets_cloud.py \
     --arguments \
       --epochs 100 \
       --batch_size 32 \
       --use_gpu
   ```

---

## Option 4: Local GPU Training (Fastest if you have NVIDIA GPU)

### Requirements:
- NVIDIA GPU with CUDA support (RTX 3090, 4090, A100, etc.)
- CUDA 11.8+ installed
- cuDNN installed

### Steps:

1. **Verify GPU is detected:**
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **Run training:**
   ```bash
   cd backend
   python train_rickets_cloud.py \
     --data_dir ./data/rickets \
     --save_dir ./checkpoints \
     --epochs 100 \
     --batch_size 32 \
     --use_gpu
   ```

3. **Monitor training:**
   - Check `checkpoints/rickets_history.json` for metrics
   - View `checkpoints/rickets_curves.png` for visualization

---

## Expected Results

### Training Performance:
- **Time per epoch:** 2-4 minutes (GPU), 15-30 minutes (CPU)
- **Total training time:** 3-7 hours for 100 epochs

### Model Performance (Expected):
- **Validation Accuracy:** 85-92%
- **Validation AUC:** 0.95-0.98
- **Classes:** Normal / Mild_Rickets / Severe_Rickets

### Output Files:
```
checkpoints/
├── rickets_best.pth          # Trained model weights
├── rickets_history.json       # Training metrics
└── rickets_curves.png         # Loss/Accuracy/AUC plots
```

---

## Comparison: Cloud vs Local

| Feature | Google Colab | AWS | Azure | Local GPU |
|---------|--------------|-----|-------|-----------|
| Cost | FREE | ~$2-5/hr | ~$2-5/hr | One-time |
| Setup | 5 min | 30 min | 15 min | Done |
| GPU Power | T4 (good) | V100 (great) | V100 (great) | Depends |
| Time to train | 2-3 hrs | 1-2 hrs | 1-2 hrs | 1-2 hrs |
| Best for | Testing | Production | Enterprise | Development |

---

## Next Steps After Training

1. **Download rickets_best.pth** to your local machine
2. **Place in:** `backend/checkpoints/rickets_best.pth`
3. **Restart the API:**
   ```bash
   python main.py
   ```
4. **Test predictions** with the frontend

---

## Troubleshooting

### OOM (Out of Memory) Error:
```bash
# Reduce batch size
python train_rickets_cloud.py --batch_size 16 --use_gpu
```

### GPU not detected in Colab:
- Go to **Runtime → Change runtime type → GPU**

### Slow training:
- Check CPU/GPU usage: `nvidia-smi`
- Increase batch size if memory allows
- Use mixed precision (already enabled)

### Model not improving:
- Increase epochs: `--epochs 150`
- Reduce learning rate: `--lr 0.0005`
- Check data quality in `backend/data/rickets/`

---

## Recommended Setup

**For best results with free GPU:**
1. Use Google Colab (free, easy, works well)
2. Training: 100-150 epochs
3. Batch size: 32 (for T4), 64 (for A100)
4. Takes ~3-4 hours
5. Expected accuracy: ~90%

**For production:**
1. Use AWS SageMaker or Azure ML
2. Training: 200+ epochs
3. Use larger GPU (V100/A100)
4. Expected accuracy: ~95%+
