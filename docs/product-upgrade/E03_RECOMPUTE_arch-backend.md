# E-03 重算方法说明（tang-duobao / 20261018T072201_13772747）

- 作者：RM-架构后端；时间：2026-10-19（Asia/Shanghai）
- 目的：供评测科学家核对历史记载的 644816 像素改动量的来源。**本说明不采用 644816**；本分支实测为全通道 1,507,328、灰度 2,719。
- 数据：用户库副本（`RUBBINGMIND_RESULTS_DIR` 指向副本的 `static/results`），**只读**，读取前后文件 SHA-256 不变。

## 1. 文件与 SHA-256

路径（相对仓库 / 副本 results 根）：

| 角色 | 路径 |
|---|---|
| 运行记录 | `tang-duobao/20261018T072201_13772747/processing.json` |
| 输入 | `tang-duobao/20261018T072201_13772747/original.png` |
| 输出 | `tang-duobao/20261018T072201_13772747/restored.png` |

请在本地对上述三个文件计算 SHA-256，并与 `processing.json.outputSha256.original` / `.restored` 对照；不一致则不得计算。

## 2. 解码

```python
import cv2, numpy as np, hashlib, json
from pathlib import Path
root = Path('static/results/tang-duobao/20261018T072201_13772747')  # 或副本路径
original = (root/'original.png').read_bytes()
restored = (root/'restored.png').read_bytes()
assert hashlib.sha256(original).hexdigest() == json.loads((root/'processing.json').read_text())['outputSha256']['original']
assert hashlib.sha256(restored).hexdigest() == json.loads((root/'processing.json').read_text())['outputSha256']['restored']
before = cv2.imdecode(np.frombuffer(original, np.uint8), cv2.IMREAD_UNCHANGED)
after  = cv2.imdecode(np.frombuffer(restored, np.uint8), cv2.IMREAD_UNCHANGED)
print(before.shape, before.dtype, after.shape, after.dtype)
# 实测：彩色输入 (H,W,3) uint8；输出为灰度复制成三通道，形状相同
```

**不要**使用 `IMREAD_GRAYSCALE` 做主判据（那是历史 644816 口径的可疑来源之一，见 SPEC v3.1 对 IMREAD_GRAYSCALE 的警告）。

## 3. 全通道 pixel-equal-v1（决定 isPassthrough）

```python
diff = np.abs(before.astype(np.int32) - after.astype(np.int32))
changed = int(np.count_nonzero(np.any(diff > 0, axis=2)))
total = int(before.shape[0] * before.shape[1])
print(changed, total, changed/total)
# 实测：1507328 1507328 1.0
```

## 4. 灰度口径 gray-bt601-pixel-equal-v1（仅并列显示）

```python
g0 = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)   # 或 BGRA2GRAY；单通道原样
g1 = cv2.cvtColor(after,  cv2.COLOR_BGR2GRAY)
gd = np.abs(g0.astype(np.int32) - g1.astype(np.int32))
gray_changed = int(np.count_nonzero(gd > 0))
print(gray_changed, gray_changed/total)
# 实测：2719 约 0.0018
```

## 5. 可复现命令（本分支）

```text
python -c "from museum_processing import run_change_status; from pathlib import Path
root=Path('static/results/tang-duobao/20261018T072201_13772747')
print(run_change_status((root/'original.png').read_bytes(), (root/'restored.png').read_bytes()))"
```

字段：`changedPixelCount=1507328`，`grayChangedPixelCount=2719`，`grayCriterion='gray-bt601-pixel-equal-v1'`，`passthroughCriterion='pixel-equal-v1'`。

## 6. 关于 644816

本分支**不采用**该数字。它既不等于全通道计数，也不等于上述 BT.601 灰度计数。可能来自旧的 `IMREAD_GRAYSCALE` 解码路径、不同的裁切/缩放，或其他未记录的预处理。请评测科学家用本节步骤在同一文件上复现后给出结论。
