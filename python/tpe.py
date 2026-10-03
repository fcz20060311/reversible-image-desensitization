import numpy as np
import struct
import random
import math
import hashlib


def domain(s):
    """domain_2.m：和为 s 的像素对，一共有几对"""
    if s <= 255:
        return s + 1
    else:
        return 510 - s + 1

def rank_pair(a, b):
    """rank_2.m：像素对 (a,b) 在所有「和为 a+b 的像素对」里的排名"""
    s = a + b
    if s <= 255:
        return a
    else:
        return a - (s - 255)


def unrank_pair(s, r):
    """rank_opposite_2.m：根据排名 r，还原出「和为 s」的像素对"""
    if s <= 255:
        b = r
    else:
        b = (s - 255) + r
    return b, s - b

def encrypt_group(group, ram):
    """Encry_group.m：加密一个像素对 —— 保和替换"""
    a, b = group
    s = a + b
    num = domain(s)              # 同和的像素对总数
    r = rank_pair(a, b)          # 当前这对的排名
    en_r = (r + ram) % num       # 排名加上密钥量，在环上转一下
    return unrank_pair(s, en_r)  # 新排名 → 新像素对

def decrypt_group(group, ram):
    """Decry_group.m：解密一个像素对 —— 逆保和替换"""
    a, b = group
    s = a + b
    num = domain(s)
    r = rank_pair(a, b)
    en_r = (r - ram) % num       # 注意这里是「减」，正好把加密转回来
    return unrank_pair(s, en_r)

def process_block(block, vec1):
    """process_block.m：块内相邻像素对，链式保和替换"""
    dimen = block.shape[0]
    line = block.astype(np.int64).flatten()          # blo2line：行优先拉成一行
    for i in range(len(line) - 1):                   # 相邻像素对，链式传播
        a, b = encrypt_group((line[i], line[i + 1]), vec1[i])
        line[i], line[i + 1] = a, b
    return line.reshape(dimen, dimen, order='F').T.astype(np.uint8)

def de_process_block(block, vec1):
    """de_process_block.m：逆链式替换——从最后一对倒着来"""
    dimen = block.shape[0]
    line = block.astype(np.int64).flatten()
    for i in range(len(line) - 2, -1, -1):           # 倒序
        a, b = decrypt_group((line[i], line[i + 1]), vec1[i])
        line[i], line[i + 1] = a, b
    return line.reshape(dimen, dimen, order='F').T.astype(np.uint8)

def per_orders(vec):
    return np.argsort(vec)[::-1]

def re_orders(orders):
    inv=np.empty_like(orders)
    inv[orders]=np.arange(len(orders))
    return inv

def hex2float(hex8):
    """8位hex → 32bit浮点；指数全1时(会得到inf/nan)返回 0，复刻老师 bin2float 的行为"""
    x = struct.unpack('>f', bytes.fromhex(hex8))[0]
    if math.isnan(x) or math.isinf(x):
        return 0.0
    return x

def key_decon(key_hex):
    """KeyDecon.m：256bit 密钥 → (x1, y1, a, b, r)"""
    x1 = hex2float(key_hex[0:8])
    y1 = hex2float(key_hex[8:16])
    a  = int(key_hex[16:24], 16) % 100 + 1
    b  = int(key_hex[24:32], 16) % 100 + 1
    dec_r = int(key_hex[32:64], 16) % (2 ** 32)
    rng = random.Random(dec_r)
    r  = rng.randint(1, 1000) + 500
    return x1, y1, a, b, r

def two_D_LSM(x1, y1, a, b):
    """two_D_LSM.m：2D-LSM 混沌映射"""
    x = math.cos(4 * a * x1 * (1 - x1) + b * math.sin(math.pi * y1) + 1)
    y = math.cos(4 * a * y1 * (1 - y1) + b * math.sin(math.pi * x1) + 1)
    return x, y

def chaos(group_num, x1, y1, a, b, t):
    """chaos.m：生成 vec1(替换用) 和 vec2(置换用)"""
    t = t + 500                                    # 预热次数
    n_iter = group_num + 1 + t
    x = np.zeros(n_iter + 1)
    y = np.zeros(n_iter + 1)
    x[0] = math.fmod(x1, 1.0)                      # rem(x1,1)：取小数部分
    y[0] = math.fmod(y1, 1.0)
    for i in range(n_iter):                        # 反复迭代
        x[i + 1], y[i + 1] = two_D_LSM(x[i], y[i], a, b)
    vec1 = x[t + 1 : t + 1 + group_num]            # 丢掉前 t+1 个，取 group_num 个
    vec2 = y[t + 1 : t + 1 + group_num + 1]        # 取 group_num+1 个
    return vec1, vec2

def _next_key(block, key_hex):
    """密钥链：下一个块的密钥 = SHA256(块前64像素 + 当前密钥)"""
    data = block.flatten()[:64].astype(np.uint8).tobytes() + key_hex.encode('ascii')
    return hashlib.sha256(data).hexdigest()

def encrypt_channel(channel, dimen, key_hex):
    """Encryption.m：对单通道灰度图加密"""
    group_num = dimen * dimen - 1
    h, w = channel.shape
    out = channel.copy()
    for i in range(h // dimen):
        for j in range(w // dimen):
            x1, y1, a, b, r = key_decon(key_hex)
            vec1, vec2 = chaos(group_num, x1, y1, a, b, r)
            vec1 = np.round(np.abs(vec1) * 100000).astype(np.int64)

            bx0, bx1 = i * dimen, (i + 1) * dimen
            by0, by1 = j * dimen, (j + 1) * dimen
            block = channel[bx0:bx1, by0:by1]

            after_b = process_block(block, vec1)              # ① 替换
            orders = per_orders(vec2)                         # ② 置换
            blo_t = after_b.flatten(order='F')[orders].reshape(dimen, dimen, order='F')
            out[bx0:bx1, by0:by1] = blo_t
            key_hex = _next_key(block, key_hex)               # ③ 密钥链
    return out, key_hex

def decrypt_channel(channel, dimen, key_hex):
    """Decryption.m：对单通道灰度图解密（顺序与加密相反）"""
    group_num = dimen * dimen - 1
    h, w = channel.shape
    out = channel.copy()
    for i in range(h // dimen):
        for j in range(w // dimen):
            x1, y1, a, b, r = key_decon(key_hex)
            vec1, vec2 = chaos(group_num, x1, y1, a, b, r)
            vec1 = np.round(np.abs(vec1) * 100000).astype(np.int64)

            bx0, bx1 = i * dimen, (i + 1) * dimen
            by0, by1 = j * dimen, (j + 1) * dimen
            block = channel[bx0:bx1, by0:by1]

            orders = per_orders(vec2)                         # ① 逆置换
            inv = re_orders(orders)
            de_t = block.flatten(order='F')[inv].reshape(dimen, dimen, order='F')
            after_block = de_process_block(de_t, vec1)        # ② 逆替换
            out[bx0:bx1, by0:by1] = after_block
            key_hex = _next_key(after_block, key_hex)         # ③ 密钥链
    return out, key_hex

def encrypt_image(img, dimen, key_hex):
    """R→G→B 依次加密（通道级链）"""
    R, k1 = encrypt_channel(img[:, :, 0], dimen, key_hex)
    G, k2 = encrypt_channel(img[:, :, 1], dimen, k1)
    B, k3 = encrypt_channel(img[:, :, 2], dimen, k2)
    return np.stack([R, G, B], axis=2), k3

def decrypt_image(img, dimen, key_hex):
    """R→G→B 依次解密"""
    R, k1 = decrypt_channel(img[:, :, 0], dimen, key_hex)
    G, k2 = decrypt_channel(img[:, :, 1], dimen, k1)
    B, k3 = decrypt_channel(img[:, :, 2], dimen, k2)
    return np.stack([R, G, B], axis=2), k3

if __name__ == "__main__":

    # ---- 1) 一个看得懂的示例 ----
    a, b = 100, 150
    ram = 12345
    print("示例 原像素对:", (a, b), " 和 =", a + b)
    e = encrypt_group((a, b), ram)
    print("示例 加密后:  ", e, " 和 =", sum(e))
    d = decrypt_group(e, ram)
    print("示例 解密后:  ", d, " 和 =", sum(d))
    print("示例 无损还原?", d == (a, b))

    # ---- 2) 穷举压力测试：所有像素对 × 随机密钥，验证「保和」和「可逆」 ----
    ok = True
    for a in range(256):
        for b in range(256):
            for _ in range(3):
                ram = random.randint(0, 10 ** 6)
                e = encrypt_group((a, b), ram)
                if sum(e) != a + b:
                    ok = False          # 和没保住 → 失败
                if decrypt_group(e, ram) != (a, b):
                    ok = False          # 还原不了 → 失败
    print("穷举测试（256×256 对 ×3 次密钥）:", "全部通过 [OK]" if ok else "有失败 [FAIL]")
    # ---- 3) 整块链式替换的可逆性 ----
    blk = np.arange(64, dtype=np.uint8).reshape(8, 8)
    vec1 = np.array([i * 100 + 7 for i in range(63)], dtype=np.int64)
    enc = process_block(blk, vec1)
    dec = de_process_block(enc, vec1)
    print("整块替换 + 逆替换，和原块一致?", np.array_equal(blk, dec))

    # ---- 4) 置换的可逆性 ----
    vec = np.array([3.2, 1.5, 4.7, 2.1, 5.0, 0.8, 6.3, 1.1])
    orders = per_orders(vec)
    arr = np.array([10, 20, 30, 40, 50, 60, 70, 80])
    shuffled = arr[orders]
    inv = re_orders(orders)
    restored = shuffled[inv]
    print("置换可逆?", np.array_equal(arr, restored))

    # ---- 5) 密钥分解 ----
    key = "357538782F413F4428472B4B6250655368566D59703373367639792442264528"
    x1, y1, a, b, r = key_decon(key)
    print("x1 =", x1)
    print("y1 =", y1)
    print("a  =", a)
    print("b  =", b)
    print("r  =", r)

    # ---- 6) 混沌映射 ----
    key = "357538782F413F4428472B4B6250655368566D59703373367639792442264528"
    x1, y1, a, b, r = key_decon(key)
    vec1, vec2 = chaos(63, x1, y1, a, b, r)     # group_num = 8*8-1 = 63
    print("vec1 长度:", len(vec1), "（应为 63）")
    print("vec2 长度:", len(vec2), "（应为 64）")
    print("vec1 前 5 个:", vec1[:5])

    # ---- 7) 端到端：一张小图加解密 ----
    key = "357538782F413F4428472B4B6250655368566D59703373367639792442264528"
    np.random.seed(0)
    img = np.random.randint(0, 256, (16, 16, 3), dtype=np.uint8)   # 16×16 随机图
    enc, _ = encrypt_image(img, 8, key)
    dec, _ = decrypt_image(enc, 8, key)
    print("端到端：加密再解密，和原图一致?", np.array_equal(img, dec))