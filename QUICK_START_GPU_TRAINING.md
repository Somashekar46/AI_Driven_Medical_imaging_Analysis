# 🚀 Quick Start: Train Rickets Model with FREE GPU

## 30-Second Summary

Your medical-ai project has:
- ✅ **CMVD Model:** Trained (95.6% AUC) - Ready to use
- ⏳ **Rickets Model:** Dataset prepared - Needs training

This guide gets your Rickets model trained on **free Google Colab GPU in ~3 hours**.

---

## Method 1: Google Colab (Easiest - FREE)

### Step 1: Prepare Google Drive
```
1. Go to Google Drive (drive.google.com)
2. Upload your "medical-ai" folder to Drive root
3. You should have: Drive/medical-ai/backend/data/rickets/
```

### Step 2: Open in Google Colab
```
1. Go to colab.research.google.com
2. File → Open notebook → GitHub
3. Search for this notebook in your drive OR
4. Upload "Rickets_Training_Colab.ipynb" file
```

### Step 3: Run Training
```
1. Runtime → Change runtime type → Select GPU (T4)
2. Run Cell 1-8 in order
3. Wait ~3 hours
4. Download your model files
```

### Step 4: Use Trained Model
```
1. Download rickets_best.pth from Colab
2. Place in: backend/checkpoints/rickets_best.pth
3. Restart your API: python main.py
4. Use frontend to test predictions
```

---

## Method 2: AWS SageMaker (Professional - PAID)

```bash
# Cost: ~$1-2 per training session
# Speed: 1-2 hours (faster than Colab)

1. Create AWS account
2. Upload data to S3
3. Launch SageMaker notebook
4. Run: python train_rickets_cloud.py --use_gpu --epochs 100
5. Download model
```

See `CLOUD_GPU_TRAINING.md` for full setup.

---

## Method 3: Local GPU (Fastest if you have NVIDIA GPU)

```bash
# Only works if you have NVIDIA GPU installed with CUDA

cd backend
python train_rickets_cloud.py --use_gpu --epochs 100 --batch_size 32
```

Check if you have GPU:
```bash
python -c "import torch; print('GPU Available:', torch.cuda.is_available())"
```

---

## Expected Results

After training completes:

```
✓ rickets_best.pth     (trained model - 200MB)
✓ rickets_history.json (training metrics)
✓ rickets_curves.png   (visualization)
```

**Performance Metrics:**
- Validation Accuracy: 85-92%
- Validation AUC: 0.95-0.98
- Classes: Normal / Mild_Rickets / Severe_Rickets

---

## File Structure After Training

```
medical-ai/
├── backend/
│   ├── checkpoints/
│   │   ├── cmvd_best.pth         ✅ (already exists)
│   │   ├── rickets_best.pth       ⏳ (will be created)
│   │   ├── rickets_history.json   ⏳ (will be created)
│   │   └── rickets_curves.png     ⏳ (will be created)
│   ├── train_rickets_cloud.py     ✅ (GPU training script)
│   ├── main.py
│   └── data/
│       ├── cmvd/train & /val      ✅
│       └── rickets/train & /val   ✅
│
├── Rickets_Training_Colab.ipynb   ✅ (Colab notebook)
├── CLOUD_GPU_TRAINING.md          ✅ (detailed guide)
└── README.md                      ✅ (updated)
```

---

## Troubleshooting

### "GPU not detected" in Colab
→ Runtime → Change runtime type → GPU

### "Out of Memory" error
→ Reduce batch size: `--batch_size 16`

### "Dataset not found" error
→ Make sure Dataset/Rickets is in your Google Drive

### Training too slow
→ Use Colab (free GPU) or AWS (faster GPU)

### Want different training parameters
```bash
python train_rickets_cloud.py \
  --epochs 150 \
  --batch_size 64 \
  --lr 0.0005 \
  --use_gpu
```

---

## Next Steps After Training

1. **Download model** from Colab
2. **Copy to local machine:** `backend/checkpoints/rickets_best.pth`
3. **Restart API:**
   ```bash
   cd backend
   python main.py
   ```
4. **Test frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
5. **Upload X-ray images** and get predictions!

---

## For More Details

- 📖 Full guide: `CLOUD_GPU_TRAINING.md`
- 🐍 Training script: `backend/train_rickets_cloud.py`
- 📓 Colab notebook: `Rickets_Training_Colab.ipynb`
- 📝 Project README: `README.md`

---

## Support

**Questions?** Check these files in order:
1. `CLOUD_GPU_TRAINING.md` - Common issues
2. `Rickets_Training_Colab.ipynb` - Step-by-step
3. `train_rickets_cloud.py` - Technical details

Good luck! 🎉
