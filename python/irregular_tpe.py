"""稀疏锚点自同步的不规则区域可逆加密 —— 老师最终实验 MATLAB 的 Python 移植

对应 MATLAB 文件：
  build_microcell_guide.m          -> build_microcell_guide
  prepare_sparse_anchor_partition.m -> select_base_anchors + reconstruct_guide
  （Phase 2/3 会继续补：边缘图、分割、合并、加解密主流程）

Phase 1 只做「分区地基」：微单元引导图 + 规则锚点 + 插值重建引导图。
"""
import numpy as np
import cv2
import hashlib

from tpe import key_decon, chaos, encrypt_group, decrypt_group, per_orders, re_orders


# ---------------------------------------------------------------------------
# build_microcell_guide.m
# ---------------------------------------------------------------------------
def partition_axis(axis_length, cell_size):
    """把长度为 axis_length 的轴切成 cell_size 大小的小段。

    返回 1-based 的 (starts, ends)；如果最后一段退化（只剩 1 个像素），并入前一段。
    """
    starts = list(range(1, axis_length + 1, cell_size))
    ends = [min(s + cell_size - 1, axis_length) for s in starts]
    if len(starts) > 1 and ends[-1] == starts[-1]:
        ends[-2] = ends[-1]
        starts = starts[:-1]
        ends = ends[:-1]
    return np.array(starts, dtype=np.int64), np.array(ends, dtype=np.int64)


def build_microcell_guide(img, cell_size=2):
    """切微单元，算每个单元的「精确像素和」和「均值引导图」。

    参数:
        img: uint8 的 HxW 或 HxWx3 图像
        cell_size: 微单元边长（老师默认 2）

    返回:
        guide:      (n_rows, n_cols, C) uint8 均值引导图（低频图）
        cell_map:   (H, W) int32，标记每个像素属于第几个单元（1-based）
        cell_sums:  (n_cells, C) uint32，每个单元的精确像素和
        cell_bounds:(n_cells, 4) [row_start, row_end, col_start, col_end]（1-based）
    """
    h, w = img.shape[:2]
    c = img.shape[2] if img.ndim == 3 else 1
    row_starts, row_ends = partition_axis(h, cell_size)
    col_starts, col_ends = partition_axis(w, cell_size)
    n_rows = len(row_starts)
    n_cols = len(col_starts)
    n_cells = n_rows * n_cols

    guide = np.zeros((n_rows, n_cols, c), dtype=np.uint8)
    cell_map = np.zeros((h, w), dtype=np.int32)
    cell_sums = np.zeros((n_cells, c), dtype=np.uint64)
    cell_bounds = np.zeros((n_cells, 4), dtype=np.int64)

    cell_id = 0
    for r in range(n_rows):
        rs = int(row_starts[r]) - 1          # 转 0-based 切片起点
        re = int(row_ends[r])                # 0-based 切片终点（开区间）
        for col in range(n_cols):
            cs = int(col_starts[col]) - 1
            ce = int(col_ends[col])
            cell_map[rs:re, cs:ce] = cell_id + 1          # 1-based 单元号
            cell_bounds[cell_id] = [
                row_starts[r], row_ends[r], col_starts[col], col_ends[col],
            ]
            pixel_count = (re - rs) * (ce - cs)
            for ch in range(c):
                block = img[rs:re, cs:ce, ch] if img.ndim == 3 else img[rs:re, cs:ce]
                s = int(block.sum())
                cell_sums[cell_id, ch] = s
                # 四舍五入（round-half-up），等价于 MATLAB 的 idivide 舍入
                guide[r, col, ch] = (s + pixel_count // 2) // pixel_count
            cell_id += 1

    return guide, cell_map, cell_sums, cell_bounds


# ---------------------------------------------------------------------------
# prepare_sparse_anchor_partition.m 里的锚点 + 重建部分
# ---------------------------------------------------------------------------
def _include_last(coords, last):
    coords = list(coords)
    if not coords or coords[-1] != last:
        coords.append(last)
    return np.array(coords, dtype=np.int64)


def select_base_anchors(guide, anchor_stride=2):
    """规则稀疏锚点：每 anchor_stride 个单元取一个（强制包含最后一行/列）。

    返回 (mask, anchor_rows, anchor_columns)：
        mask: (n_rows, n_cols) bool，锚点单元为 True
        anchor_rows / anchor_columns: 1-based 锚点坐标
    """
    h, w = guide.shape[:2]
    ar = _include_last(range(1, h + 1, anchor_stride), h)
    ac = _include_last(range(1, w + 1, anchor_stride), w)
    mask = np.zeros((h, w), dtype=bool)
    mask[np.ix_(ar - 1, ac - 1)] = True
    return mask, ar, ac


def reconstruct_guide(guide, anchor_rows, anchor_columns):
    """只靠锚点单元的值，用双线性插值重建整张引导图。

    等价于 MATLAB 的 reconstruct_guide：先横向 interp1、再纵向 interp1。
    只要锚点值不变，重建结果就完全一致（这是「自同步」的根基）。
    """
    h, w = guide.shape[:2]
    c = guide.shape[2] if guide.ndim == 3 else 1
    recon = np.zeros_like(guide)
    ar = anchor_rows - 1          # 0-based
    ac = anchor_columns - 1

    for ch in range(c):
        ch_data = guide[..., ch] if guide.ndim == 3 else guide
        samples = ch_data[np.ix_(ar, ac)].astype(np.float64)   # (len(ar), len(ac))

        # 横向：对每个锚点行，沿列方向线性插值
        horizontal = np.zeros((len(ar), w), dtype=np.float64)
        for i in range(len(ar)):
            horizontal[i, :] = np.interp(np.arange(w), ac, samples[i, :])

        # 纵向：对每个列，沿行方向线性插值
        channel = np.zeros((h, w), dtype=np.float64)
        for j in range(w):
            channel[:, j] = np.interp(np.arange(h), ar, horizontal[:, j])

        recon[..., ch] = np.clip(np.round(channel), 0, 255).astype(np.uint8)

    return recon


# ---------------------------------------------------------------------------
# Phase 2: 轮廓级不规则分区（分水岭）
# ---------------------------------------------------------------------------
def segment_guide(guide, target_area=256):
    """在引导图（单元均值图）上做分水岭，得到「沿边缘」的不规则区域。

    返回 labels: (n_rows, n_cols) int32，每个单元的区域号（1-based，连续）。
    """
    h, w = guide.shape[:2]
    if guide.ndim == 2:
        img3 = cv2.cvtColor(guide, cv2.COLOR_GRAY2BGR)
    else:
        img3 = cv2.cvtColor(guide, cv2.COLOR_RGB2BGR)

    # 网格种子（和老师 SLIC 里 seed_step 的思路一致）
    n_regions = max(16, min(int(round(h * w / target_area)), 3000))
    step = max(2, int(round(np.sqrt(h * w / n_regions))))
    markers = np.zeros((h, w), dtype=np.int32)
    k = 1
    for r in range(step // 2, h, step):
        for c in range(step // 2, w, step):
            markers[r, c] = k
            k += 1

    # 分水岭（cv2 内部会自己算梯度地形）
    cv2.watershed(img3, markers)

    # 分水岭把「脊线」标成 -1，需要把它们并进最近区域
    labels = markers.copy()
    labels[labels == -1] = 0
    for _ in range(200):
        zero = labels == 0
        if not zero.any():
            break
        rr, cc = np.where(zero)
        for r, c in zip(rr, cc):
            r0, r1 = max(0, r - 1), min(h, r + 2)
            c0, c1 = max(0, c - 1), min(w, c + 2)
            nb = labels[r0:r1, c0:c1]
            nb = nb[nb > 0]
            if nb.size:
                labels[r, c] = int(np.bincount(nb).argmax())

    # 重新编号成连续的 1..N（分水岭可能合并种子，标签会有空洞）
    unique = np.unique(labels)
    unique = unique[unique > 0]
    mapping = np.zeros(int(labels.max()) + 1, dtype=np.int32)
    mapping[unique] = np.arange(1, len(unique) + 1, dtype=np.int32)
    return mapping[labels]


def build_partition(img, cell_size=2, anchor_stride=3, target_area=None):
    """完整分区：微单元 → 锚点 → 重建引导图 → 分水岭分割 → 不规则区域。

    返回 partition 字典，加密和解密共用（必须确定性，才能自同步）。
    默认参数对齐老师实验：anchor_stride=3，目标约 20 个不规则区域。
    """
    if target_area is None:
        h, w = img.shape[:2]
        guide_area = (-(-h // cell_size)) * (-(-w // cell_size))
        target_area = max(16, int(round(guide_area / 20)))

    guide, cell_map, cell_sums, cell_bounds = build_microcell_guide(img, cell_size)
    anchor_mask, ar, ac = select_base_anchors(guide, anchor_stride)
    recon = reconstruct_guide(guide, ar, ac)
    cell_labels = segment_guide(recon, target_area)

    n_cells = cell_sums.shape[0]
    flat_labels = cell_labels.reshape(-1)               # 与 cell_id 一一对应

    num_regions = int(flat_labels.max())
    region_cells = [[] for _ in range(num_regions)]
    for cell_id in range(1, n_cells + 1):
        lab = int(flat_labels[cell_id - 1])
        region_cells[lab - 1].append(cell_id)

    anchor_flat = anchor_mask.reshape(-1)
    anchor_cell_ids = (np.where(anchor_flat)[0] + 1).astype(np.int64)

    return {
        "cell_size": cell_size,
        "guide": guide,
        "cell_map": cell_map,
        "cell_sums": cell_sums,
        "cell_bounds": cell_bounds,
        "reconstructed_guide": recon,
        "cell_labels": cell_labels,
        "region_cells": region_cells,
        "anchor_cell_ids": anchor_cell_ids,
    }


# ---------------------------------------------------------------------------
# Phase 3: 加密 / 解密主流程
# ---------------------------------------------------------------------------
def irregular_key_update(original_values, key_hex):
    """irregular_key_update.m：下一个区域的密钥 = SHA256(整区域原始像素 + 当前密钥)"""
    data = np.asarray(original_values, dtype=np.uint8).reshape(-1).tobytes() + key_hex.encode("ascii")
    return hashlib.sha256(data).hexdigest()


def tpe_encrypt_vector(values, key_hex):
    """teacher_tpe_encrypt_vector.m：对可变长度像素向量做保和替换 + 置换"""
    values = np.asarray(values, dtype=np.int64).reshape(-1)
    n = values.shape[0]
    x1, y1, a, b, r = key_decon(key_hex)
    vec1, vec2 = chaos(n - 1, x1, y1, a, b, r)
    vec1 = np.round(np.abs(vec1) * 100000).astype(np.int64)

    work = values.copy()
    for i in range(n - 1):
        p, q = encrypt_group((work[i], work[i + 1]), vec1[i])
        work[i], work[i + 1] = p, q
    enc = work[per_orders(vec2)]
    return enc.astype(np.uint8), irregular_key_update(values, key_hex)


def tpe_decrypt_vector(values, key_hex):
    """teacher_tpe_decrypt_vector.m：先逆置换，再逆链式替换"""
    values = np.asarray(values, dtype=np.int64).reshape(-1)
    n = values.shape[0]
    x1, y1, a, b, r = key_decon(key_hex)
    vec1, vec2 = chaos(n - 1, x1, y1, a, b, r)
    vec1 = np.round(np.abs(vec1) * 100000).astype(np.int64)

    work = values[re_orders(per_orders(vec2))]      # 逆置换
    for i in range(n - 2, -1, -1):                  # 逆链式替换
        p, q = decrypt_group((work[i], work[i + 1]), vec1[i])
        work[i], work[i + 1] = p, q
    return work.astype(np.uint8), irregular_key_update(work, key_hex)


def tpe_encrypt_cells(cells, key_hex):
    """teacher_tpe_encrypt_cells.m：同一批锚点单元共享一次混沌序列，逐单元保和加密"""
    sizes = [len(c) for c in cells]
    total = sum(sizes)
    x1, y1, a, b, r = key_decon(key_hex)
    vec1, vec2 = chaos(total - 1, x1, y1, a, b, r)
    vec1 = np.round(np.abs(vec1) * 100000).astype(np.int64)

    enc_cells, rep_off, perm_off = [], 0, 0
    for c in cells:
        vals = np.asarray(c, dtype=np.int64).copy()
        m = len(vals)
        for i in range(m - 1):
            p, q = encrypt_group((vals[i], vals[i + 1]), vec1[rep_off + i])
            vals[i], vals[i + 1] = p, q
        enc_cells.append(vals[per_orders(vec2[perm_off:perm_off + m])].astype(np.uint8))
        rep_off += m - 1
        perm_off += m
    orig = np.concatenate([np.asarray(c).reshape(-1) for c in cells])
    return enc_cells, irregular_key_update(orig, key_hex)


def tpe_decrypt_cells(cells, key_hex):
    """teacher_tpe_decrypt_cells.m：锚点单元的逆操作"""
    sizes = [len(c) for c in cells]
    total = sum(sizes)
    x1, y1, a, b, r = key_decon(key_hex)
    vec1, vec2 = chaos(total - 1, x1, y1, a, b, r)
    vec1 = np.round(np.abs(vec1) * 100000).astype(np.int64)

    dec_cells, rep_off, perm_off = [], 0, 0
    for c in cells:
        vals = np.asarray(c, dtype=np.int64).copy()
        m = len(vals)
        vals = vals[re_orders(per_orders(vec2[perm_off:perm_off + m]))]
        for i in range(m - 2, -1, -1):
            p, q = decrypt_group((vals[i], vals[i + 1]), vec1[rep_off + i])
            vals[i], vals[i + 1] = p, q
        dec_cells.append(vals.astype(np.uint8))
        rep_off += m - 1
        perm_off += m
    orig = np.concatenate([np.asarray(c).reshape(-1) for c in dec_cells])
    return dec_cells, irregular_key_update(orig, key_hex)


def _cell_slice(part, cid):
    r0, r1, c0, c1 = part["cell_bounds"][cid - 1]
    return r0 - 1, r1, c0 - 1, c1      # 0-based [rs:re, cs:ce]


def _cell_pixels(channel, part, cid):
    rs, re, cs, ce = _cell_slice(part, cid)
    return channel[rs:re, cs:ce].reshape(-1)


def _scatter_cell(channel, part, cid, values):
    rs, re, cs, ce = _cell_slice(part, cid)
    channel[rs:re, cs:ce] = values.reshape(re - rs, ce - cs)


def _region_pixel_values(channel, part, cids):
    return np.concatenate([_cell_pixels(channel, part, cid) for cid in cids])


def _scatter_region(channel, part, cids, values):
    off = 0
    for cid in cids:
        rs, re, cs, ce = _cell_slice(part, cid)
        n = (re - rs) * (ce - cs)
        channel[rs:re, cs:ce] = values[off:off + n].reshape(re - rs, ce - cs)
        off += n


def encrypt_image_irregular(img, key_hex, cell_size=2, anchor_stride=3, target_area=None):
    """sparse_anchor_irregular_encrypt.m：稀疏锚点自同步的不规则区域加密"""
    part = build_partition(img, cell_size, anchor_stride, target_area)
    anchor_set = set(int(x) for x in part["anchor_cell_ids"])

    chs = [img] if img.ndim == 2 else [img[..., ch] for ch in range(img.shape[2])]
    out_chs, current_key = [], key_hex

    for src in chs:
        tgt = src.copy()
        for region_cells in part["region_cells"]:
            anchor_ids = [cid for cid in region_cells if cid in anchor_set]
            nonanchor_ids = [cid for cid in region_cells if cid not in anchor_set]
            if anchor_ids:
                vecs = [_cell_pixels(src, part, cid) for cid in anchor_ids]
                enc, current_key = tpe_encrypt_cells(vecs, current_key)
                for cid, ev in zip(anchor_ids, enc):
                    _scatter_cell(tgt, part, cid, ev)
            if nonanchor_ids:
                vals = _region_pixel_values(src, part, nonanchor_ids)
                if vals.size >= 2:
                    enc_vals, current_key = tpe_encrypt_vector(vals, current_key)
                    _scatter_region(tgt, part, nonanchor_ids, enc_vals)
        out_chs.append(tgt)

    out = np.stack(out_chs, axis=2) if img.ndim == 3 else out_chs[0]
    return out, current_key


def decrypt_image_irregular(img, key_hex, cell_size=2, anchor_stride=3, target_area=None):
    """sparse_anchor_irregular_decrypt.m：仅由密文本身重建分区并精确解密"""
    part = build_partition(img, cell_size, anchor_stride, target_area)
    anchor_set = set(int(x) for x in part["anchor_cell_ids"])

    chs = [img] if img.ndim == 2 else [img[..., ch] for ch in range(img.shape[2])]
    out_chs, current_key = [], key_hex

    for src in chs:
        tgt = src.copy()
        for region_cells in part["region_cells"]:
            anchor_ids = [cid for cid in region_cells if cid in anchor_set]
            nonanchor_ids = [cid for cid in region_cells if cid not in anchor_set]
            if anchor_ids:
                vecs = [_cell_pixels(src, part, cid) for cid in anchor_ids]
                dec, current_key = tpe_decrypt_cells(vecs, current_key)
                for cid, dv in zip(anchor_ids, dec):
                    _scatter_cell(tgt, part, cid, dv)
            if nonanchor_ids:
                vals = _region_pixel_values(src, part, nonanchor_ids)
                if vals.size >= 2:
                    dec_vals, current_key = tpe_decrypt_vector(vals, current_key)
                    _scatter_region(tgt, part, nonanchor_ids, dec_vals)
        out_chs.append(tgt)

    out = np.stack(out_chs, axis=2) if img.ndim == 3 else out_chs[0]
    return out, current_key


if __name__ == "__main__":
    # 自检：随机小图 -> 切微单元 -> 选锚点 -> 重建 -> 锚点处应精确还原
    np.random.seed(1)
    img = np.random.randint(0, 256, (16, 20, 3), dtype=np.uint8)

    guide, cell_map, cell_sums, cell_bounds = build_microcell_guide(img, cell_size=2)
    print("引导图尺寸:", guide.shape, " 单元数:", cell_sums.shape[0])

    mask, ar, ac = select_base_anchors(guide, anchor_stride=2)
    print("锚点行:", ar, " 锚点列:", ac, " 锚点占比: %.1f%%" % (100 * mask.mean()))

    recon = reconstruct_guide(guide, ar, ac)

    # 锚点处：重建值应和原引导图完全一致
    anchor_equal = np.array_equal(
        recon[np.ix_(ar - 1, ac - 1)], guide[np.ix_(ar - 1, ac - 1)]
    )
    print("锚点处重建精确一致?", anchor_equal)

    # 非锚点处：允许有误差，只报一下平均差
    diff = np.abs(recon.astype(int) - guide.astype(int))
    print("重建平均绝对误差:", round(float(diff.mean()), 3))

    # ---- Phase 2: 分水岭分割 + 建分区 ----
    part = build_partition(img, cell_size=2, anchor_stride=2, target_area=256)
    sizes = [len(rc) for rc in part["region_cells"]]
    print("区域数:", len(part["region_cells"]))
    print("每区域单元数 min/mean/max:", min(sizes), round(sum(sizes) / len(sizes), 1), max(sizes))
    print("锚点单元数:", len(part["anchor_cell_ids"]))
    # 分区是否覆盖所有单元、无遗漏无重复
    all_cells = [c for rc in part["region_cells"] for c in rc]
    print("分区覆盖完整且无重复?", len(all_cells) == cell_sums.shape[0] and len(set(all_cells)) == len(all_cells))

    # ---- Phase 3: 不规则加密端到端往返 ----
    key = "357538782F413F4428472B4B6250655368566D59703373367639792442264528"
    enc, _ = encrypt_image_irregular(img, key, cell_size=2, anchor_stride=2, target_area=256)
    dec, _ = decrypt_image_irregular(enc, key, cell_size=2, anchor_stride=2, target_area=256)
    print("不规则加密端到端：无损还原?", np.array_equal(img, dec))
    # 加密图应该明显「看不清」：和原图差别很大（非锚点被打散）
    print("密文与原图差异(平均绝对误差):", round(float(np.abs(enc.astype(int) - img.astype(int)).mean()), 1))
