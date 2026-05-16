"""
Coronary Microvascular Dysfunction (CMVD) Detection Model — v2
NO image validation — model handles all inputs directly
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import io
import numpy as np


class ChannelAttention(nn.Module):
    def __init__(self, in_channels, reduction=16):
        super().__init__()
        mid = max(in_channels // reduction, 8)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(in_channels, mid, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(mid, in_channels, bias=False)
        )
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        b, c, _, _ = x.size()
        a = self.fc(self.avg_pool(x).view(b, c))
        m = self.fc(self.max_pool(x).view(b, c))
        return self.sigmoid((a + m).view(b, c, 1, 1)) * x


class SpatialAttention(nn.Module):
    def __init__(self, kernel_size=7):
        super().__init__()
        self.conv = nn.Conv2d(2, 1, kernel_size, padding=kernel_size // 2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        avg = torch.mean(x, dim=1, keepdim=True)
        mx, _ = torch.max(x, dim=1, keepdim=True)
        return self.sigmoid(self.conv(torch.cat([avg, mx], dim=1))) * x


class CBAM(nn.Module):
    def __init__(self, in_channels):
        super().__init__()
        self.ch = ChannelAttention(in_channels)
        self.sp = SpatialAttention()

    def forward(self, x):
        return self.sp(self.ch(x))


class CMVDNet(nn.Module):
    def __init__(self, num_classes=2, pretrained=False):
        super().__init__()
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        bb = models.resnet50(weights=weights)

        self.stem    = nn.Sequential(bb.conv1, bb.bn1, bb.relu, bb.maxpool)
        self.layer1  = bb.layer1
        self.layer2  = bb.layer2
        self.layer3  = bb.layer3
        self.layer4  = bb.layer4
        self.avgpool = bb.avgpool
        self.cbam3   = CBAM(1024)
        self.cbam4   = CBAM(2048)

        self.classifier = nn.Sequential(
            nn.Linear(2048, 512),
            nn.BatchNorm1d(512),
            nn.GELU(),
            nn.Dropout(0.4),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        x = self.stem(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.cbam3(x)
        x = self.layer4(x)
        x = self.cbam4(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        return self.classifier(x)


class CMVDPreprocessor:
    BASE = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ])

    def preprocess(self, image_bytes):
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return self.BASE(img).unsqueeze(0)


class CMVDDetector:
    CLASSES = ["Normal", "CMVD Detected"]

    def __init__(self, model_path="checkpoints/cmvd_best.pth", device="cpu", num_classes=2):
        self.device = torch.device(device)
        self.model  = CMVDNet(num_classes=num_classes, pretrained=False)
        self.preprocessor = CMVDPreprocessor()

        print(f"Loading CMVD model: {model_path}")
        ckpt = torch.load(model_path, map_location=self.device, weights_only=False)

        if isinstance(ckpt, dict):
            if "model_state_dict" in ckpt:
                state_dict = ckpt["model_state_dict"]
            elif "model" in ckpt:
                state_dict = ckpt["model"]
            else:
                state_dict = ckpt
        else:
            state_dict = ckpt

        self.model.load_state_dict(state_dict, strict=True)
        self.model.to(self.device).eval()
        print("✅ CMVD model loaded successfully!")

    def predict(self, image_bytes):
        # No validation — just run inference directly
        try:
            x = self.preprocessor.preprocess(image_bytes).to(self.device)
            with torch.no_grad():
                logits = self.model(x)
                probs  = F.softmax(logits, dim=1)

            conf, pred = torch.max(probs, 1)

            return {
                "condition": "Coronary Microvascular Dysfunction",
                "prediction": self.CLASSES[pred.item()],
                "confidence": round(conf.item() * 100, 2),
                "class_probabilities": {
                    c: round(probs[0][i].item() * 100, 2)
                    for i, c in enumerate(self.CLASSES)
                },
                "is_medical": True
            }
        except Exception as e:
            return {"error": f"Inference failed: {str(e)}", "is_medical": True}