from PIL import Image
from collections import deque
import numpy as np

src = r'D:\Desktop\edu point logo.jpeg'
im = Image.open(src).convert('RGB')
a = np.asarray(im)
H, W, _ = a.shape
print('input:', H, W)

white = (a[:, :, 0] >= 230) & (a[:, :, 1] >= 230) & (a[:, :, 2] >= 230)

vis = np.zeros((H, W), dtype=bool)
dq = deque()
for x in range(W):
    if white[0, x]:
        dq.append((0, x)); vis[0, x] = True
    if white[H - 1, x]:
        dq.append((H - 1, x)); vis[H - 1, x] = True
for y in range(1, H - 1):
    if white[y, 0]:
        dq.append((y, 0)); vis[y, 0] = True
    if white[y, W - 1]:
        dq.append((y, W - 1)); vis[y, W - 1] = True
while dq:
    y, x = dq.popleft()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < W and not vis[ny, nx] and white[ny, nx]:
            vis[ny, nx] = True
            dq.append((ny, nx))
print('bg px:', int(vis.sum()))

rgba = np.dstack([a, np.full((H, W), 255, np.uint8)])
rgba[vis] = (0, 0, 0, 0)

dil = np.zeros((H, W), dtype=bool)
dil[1:, :] |= vis[:-1, :]
dil[:-1, :] |= vis[1:, :]
dil[:, 1:] |= vis[:, :-1]
dil[:, :-1] |= vis[:, 1:]
boundary = dil & ~vis
minch = a.min(axis=2).astype(np.int16)
rgba[boundary, 3] = np.clip(255 - minch, 0, 255)[boundary].astype(np.uint8)

alpha = rgba[:, :, 3]
ys, xs = np.where(alpha > 0)
PAD = 10
y0 = max(0, ys.min() - PAD); y1 = min(H, ys.max() + 1 + PAD)
x0 = max(0, xs.min() - PAD); x1 = min(W, xs.max() + 1 + PAD)
out = rgba[y0:y1, x0:x1]
print('output:', out.shape)

out_img = Image.fromarray(out, 'RGBA')
base = r'D:\Desktop\б\EduPoint\static\images'
for name in ('edu_logo_v2.png', 'edu_logo_footer.png', 'edu_logo.png'):
    out_img.save(base + '\\' + name)
print('saved')
