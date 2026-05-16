"""
Nutritional Rickets Detection Model — v2 Fixed
NO image validation — model handles all inputs directly
Classes: Mild_Rickets / Normal / Severe_Rickets (alphabetical from training)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import io
import numpy as np


class RicketsNet(nn.Module):
    """
    Matches SimpleRicketsNet trained on Kaggle:
    EfficientNet-B3 + Dropout + Linear classifier
    """
    def __init__(self, num_classes=3, pretrained=False):
        super().__init__()
        weights = models.EfficientNet_B3_Weights.DEFAULT if pretrained else None
        bb = models.efficientnet_b3(weights=weights)

        self.features  = bb.features
        self.avgpool   = bb.avgpool
        in_features    = bb.classifier[1].in_features  # 1536

        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_features, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        return self.classifier(x)


class RicketsPreprocessor:
    BASE = transforms.Compose([
        transforms.Resize((300, 300)),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize([0.449, 0.449, 0.449],
                             [0.226, 0.226, 0.226]),
    ])

    def preprocess(self, image_bytes):
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return self.BASE(img).unsqueeze(0)


class RicketsDetector:
    # Alphabetical order — matches how ImageFolder loaded classes during training
    CLASSES = ["Mild_Rickets", "Normal", "Severe_Rickets"]

    VITAMIN_D = {
        "Normal":         "> 30 ng/mL (Sufficient)",
        "Mild_Rickets":   "12–30 ng/mL (Insufficient)",
        "Severe_Rickets": "< 12 ng/mL (Deficient)",
    }

    URGENCY = {
        "Normal":         "Routine checkup",
        "Mild_Rickets":   "Non-urgent — within 2 weeks",
        "Severe_Rickets": "Urgent — within 48 hours",
    }

    def __init__(self, model_path="checkpoints/rickets_best.pth", device="cpu"):
        self.device = torch.device(device)
        self.model  = RicketsNet(num_classes=3, pretrained=False)
        self.preprocessor = RicketsPreprocessor()

        print(f"Loading Rickets model: {model_path}")
        ckpt = torch.load(model_path, map_location=self.device, weights_only=True)

        # Handle different checkpoint formats
        if isinstance(ckpt, dict):
            if "model_state_dict" in ckpt:
                state_dict = ckpt["model_state_dict"]
            elif "model" in ckpt:
                state_dict = ckpt["model"]
            else:
                state_dict = ckpt
        else:
            state_dict = ckpt

        # Fix key naming mismatches
        fixed = {}
        for k, v in state_dict.items():
            if k == "classifier.weight":
                fixed["classifier.1.weight"] = v
            elif k == "classifier.bias":
                fixed["classifier.1.bias"] = v
            else:
                fixed[k] = v

        self.model.load_state_dict(fixed, strict=True)
        self.model.to(self.device).eval()
        print("✅ Rickets model loaded successfully!")

    def predict(self, image_bytes):
        # No validation — just run inference directly
        try:
            x = self.preprocessor.preprocess(image_bytes).to(self.device)
            with torch.no_grad():
                logits = self.model(x)
                probs  = F.softmax(logits, dim=1)

            conf, pred = torch.max(probs, 1)
            cls_name = self.CLASSES[pred.item()]

            return {
                "condition": "Nutritional Rickets",
                "prediction": cls_name,
                "confidence": round(conf.item() * 100, 2),
                "class_probabilities": {
                    c: round(probs[0][i].item() * 100, 2)
                    for i, c in enumerate(self.CLASSES)
                },
                "estimated_vitamin_d": self.VITAMIN_D.get(cls_name, "Unknown"),
                "urgency": self.URGENCY.get(cls_name, "Unknown"),
                "is_medical": True
            }
        except Exception as e:
            return {"error": f"Inference failed: {str(e)}", "is_medical": True}