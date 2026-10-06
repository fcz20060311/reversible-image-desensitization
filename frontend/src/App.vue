<script setup lang="ts">
import { computed, ref } from "vue";
import axios from "axios";
import type { UploadFile } from "element-plus";

const API = "http://127.0.0.1:8000";

interface Item {
  filename: string;
  regionCount: number;
  url: string; // 当前展示的图片地址（脱敏图或还原图）
  blob: Blob; // 脱敏图的字节，还原时要重新上传
}

const files = ref<File[]>([]);
const items = ref<Item[]>([]);
const key = ref("");
const keyInput = ref("");
const loading = ref(false);
const restored = ref(false); // 是否已还原 → 控制「封存牌」状态

// 所有图检测到的敏感区域总数（顶部状态栏用）
const totalRegions = computed(() => items.value.reduce((sum, it) => sum + it.regionCount, 0));

function syncFiles(fileList: UploadFile[]) {
  files.value = fileList.map((f) => f.raw).filter((f) => !!f);
}

function onChange(_file: UploadFile, fileList: UploadFile[]) {
  syncFiles(fileList);
}

function onRemove(_file: UploadFile, fileList: UploadFile[]) {
  syncFiles(fileList);
}

function base64ToBlob(b64: string): Blob {
  const chars = atob(b64);
  const bytes = new Uint8Array(chars.length);
  for (let i = 0; i < chars.length; i++) bytes[i] = chars.charCodeAt(i);
  return new Blob([bytes], { type: "image/png" });
}

async function desensitize() {
  if (!files.value.length) return;
  const form = new FormData();
  files.value.forEach((f) => form.append("files", f));

  loading.value = true;
  try {
    const resp = await axios.post(`${API}/batch_desensitize`, form);
    const data = resp.data as {
      key: string;
      images: { filename: string; region_count: number; image_base64: string }[];
    };
    key.value = data.key;
    restored.value = false;
    items.value = data.images.map((it) => {
      const blob = base64ToBlob(it.image_base64);
      return {
        filename: it.filename,
        regionCount: it.region_count,
        url: URL.createObjectURL(blob),
        blob,
      };
    });
  } catch {
    alert("批量脱敏失败，请重试");
  } finally {
    loading.value = false;
  }
}

async function restore() {
  if (!keyInput.value || !items.value.length) return;
  const form = new FormData();
  form.append("key", keyInput.value);
  items.value.forEach((it) => form.append("files", it.blob, it.filename));

  loading.value = true;
  try {
    const resp = await axios.post(`${API}/batch_restore`, form);
    const images = resp.data.images as string[];
    images.forEach((b64, i) => {
      const blob = base64ToBlob(b64);
      items.value[i].url = URL.createObjectURL(blob);
    });
    restored.value = true;
  } catch (e: any) {
    alert(e?.response?.data?.error ?? "还原失败，请检查密钥");
  } finally {
    loading.value = false;
  }
}

function copyKey() {
  navigator.clipboard.writeText(key.value);
}
</script>

<template>
  <div class="page">
    <header class="topbar">
      <div class="brand">
        <span class="brand-mark">▣</span>
        <div class="brand-text">
          <h1>AI 可逆脱敏系统</h1>
          <p class="tagline">REVERSIBLE DESENSITIZATION</p>
        </div>
      </div>
      <div class="status">
        <span class="chip" :class="{ on: items.length }">
          <span class="dot"></span>
          {{ items.length ? `已封存 ${items.length} 张 · ${totalRegions} 区域` : "待命" }}
        </span>
        <span v-if="key" class="chip key-chip">KEY {{ key.slice(0, 8) }}…</span>
      </div>
    </header>

    <div class="workbench">
      <aside class="rail">
        <el-upload
          class="dropzone"
          drag
          multiple
          :auto-upload="false"
          :on-change="onChange"
          :on-remove="onRemove"
          accept="image/*"
        >
          <div class="drop-hint">
            <div class="drop-glyph">＋</div>
            <div class="drop-title">拖入照片</div>
            <div class="drop-sub">或点击选择 · 可一次多张</div>
          </div>
        </el-upload>

        <div class="rail-row">
          <el-button class="btn-primary" :loading="loading" :disabled="!files.length" @click="desensitize">
            批量脱敏
          </el-button>
          <span class="file-count">{{ files.length ? `已选 ${files.length} 张` : "未选择文件" }}</span>
        </div>

        <div v-if="key" class="keycard">
          <div class="keycard-head">
            <span class="keycard-label">共享密钥 · SHARED KEY</span>
            <el-button class="copy-btn" text @click="copyKey">复制</el-button>
          </div>
          <div class="keycard-value">{{ key }}</div>
          <div class="keycard-note">还原时需凭此密钥 · 请妥善保存</div>
        </div>

        <div v-if="items.length" class="restore">
          <el-input v-model="keyInput" class="key-input" placeholder="输入共享密钥" clearable @keyup.enter="restore" />
          <el-button class="btn-success" :loading="loading" :disabled="!keyInput" @click="restore">
            授权还原
          </el-button>
        </div>
      </aside>

      <main class="plate">
        <div v-if="!items.length" class="empty">
          <div class="empty-glyph">◇</div>
          <p>尚未封存任何图像</p>
          <p class="empty-sub">左侧上传照片，开始一次批量脱敏</p>
        </div>

        <div v-else class="grid">
          <div v-for="(it, i) in items" :key="i" class="card">
            <div class="frame">
              <el-image :src="it.url" fit="contain" />
              <span class="corner tl"></span>
              <span class="corner tr"></span>
              <span class="corner bl"></span>
              <span class="corner br"></span>
            </div>
            <div class="card-info">
              <div class="card-name">{{ it.filename }}</div>
              <div class="seal" :class="{ open: restored }">
                {{ restored ? "已还原 · RESTORED" : `已封存 · SEALED · ${it.regionCount}` }}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style>
body {
  background: #0b0e13;
  color: #e8e4dc;
}
</style>

<style scoped>
.page {
  --void: #0b0e13;
  --slab: #151b24;
  --rule: #26303c;
  --bone: #e8e4dc;
  --brass: #c8963e;
  --tell: #6fb3a8;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px 40px;
  color: var(--bone);
}
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0 16px;
  border-bottom: 1px solid var(--rule);
  margin-bottom: 20px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.brand-mark {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 1px solid var(--brass);
  color: var(--brass);
  font-family: "JetBrains Mono", Consolas, monospace;
}
.brand-text h1 {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1px;
}
.tagline {
  font-family: "JetBrains Mono", Consolas, monospace;
  font-size: 10px;
  letter-spacing: 3px;
  color: #6b7280;
  margin-top: 2px;
}
.status {
  display: flex;
  gap: 10px;
  align-items: center;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: "JetBrains Mono", Consolas, monospace;
  font-size: 11px;
  letter-spacing: 1px;
  color: #6b7280;
  border: 1px solid var(--rule);
  padding: 5px 10px;
  border-radius: 999px;
}
.chip.on {
  color: var(--brass);
  border-color: var(--brass);
}
.chip.key-chip {
  color: var(--bone);
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4b5563;
}
.chip.on .dot {
  background: var(--brass);
  box-shadow: 0 0 6px var(--brass);
}

.workbench {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 20px;
  align-items: start;
}
.rail {
  display: flex;
  flex-direction: column;
  gap: 14px;
  position: sticky;
  top: 20px;
}
.dropzone :deep(.el-upload-dragger) {
  background: var(--slab);
  border: 1px dashed var(--rule);
  border-radius: 12px;
  padding: 26px 16px;
}
.dropzone :deep(.el-upload-dragger:hover) {
  border-color: var(--brass);
}
.drop-hint {
  text-align: center;
}
.drop-glyph {
  font-size: 24px;
  color: var(--brass);
}
.drop-title {
  color: var(--bone);
  margin-top: 8px;
  font-size: 15px;
}
.drop-sub {
  color: #6b7280;
  font-size: 12px;
  margin-top: 4px;
}
.rail-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.file-count {
  color: #6b7280;
  font-size: 12px;
}
.btn-primary {
  background: var(--brass);
  border: none;
  color: #14100a;
  font-weight: 600;
}
.btn-primary:hover {
  background: #d8a94f;
  color: #14100a;
}
.btn-success {
  background: var(--tell);
  border: none;
  color: #07110f;
  font-weight: 600;
}
.btn-success:hover {
  background: #7fc5bb;
  color: #07110f;
}

.keycard {
  background: var(--slab);
  border: 1px solid var(--rule);
  border-radius: 12px;
  padding: 14px 16px;
}
.keycard-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.keycard-label {
  font-family: "JetBrains Mono", Consolas, monospace;
  font-size: 10px;
  letter-spacing: 2px;
  color: #6b7280;
}
.copy-btn {
  color: var(--brass);
}
.keycard-value {
  font-family: "JetBrains Mono", Consolas, monospace;
  font-size: 13px;
  color: var(--bone);
  word-break: break-all;
  margin: 8px 0;
  letter-spacing: 1px;
}
.keycard-note {
  font-size: 11px;
  color: #6b7280;
}

.restore {
  display: flex;
  gap: 10px;
}
.key-input :deep(.el-input__wrapper) {
  background: var(--slab);
  box-shadow: 0 0 0 1px var(--rule) inset;
}
.key-input :deep(.el-input__inner) {
  color: var(--bone);
}

.plate {
  min-height: 480px;
}
.empty {
  border: 1px dashed var(--rule);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 480px;
  color: #6b7280;
}
.empty-glyph {
  font-size: 40px;
  color: #374151;
}
.empty p {
  margin-top: 12px;
  font-size: 14px;
}
.empty-sub {
  font-size: 12px;
  color: #4b5563;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}
.card {
  background: var(--slab);
  border: 1px solid var(--rule);
  border-radius: 12px;
  overflow: hidden;
}
.frame {
  position: relative;
}
.frame :deep(.el-image) {
  width: 100%;
  height: 200px;
  display: block;
  background: #05070a;
}
.corner {
  position: absolute;
  width: 14px;
  height: 14px;
  border-color: var(--brass);
}
.corner.tl {
  top: 8px;
  left: 8px;
  border-top: 1px solid;
  border-left: 1px solid;
}
.corner.tr {
  top: 8px;
  right: 8px;
  border-top: 1px solid;
  border-right: 1px solid;
}
.corner.bl {
  bottom: 8px;
  left: 8px;
  border-bottom: 1px solid;
  border-left: 1px solid;
}
.corner.br {
  bottom: 8px;
  right: 8px;
  border-bottom: 1px solid;
  border-right: 1px solid;
}
.card-info {
  padding: 12px 14px;
}
.card-name {
  font-size: 13px;
  color: var(--bone);
  word-break: break-all;
}
.seal {
  display: inline-block;
  margin-top: 8px;
  font-family: "JetBrains Mono", Consolas, monospace;
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--brass);
  border: 1px solid var(--brass);
  border-radius: 4px;
  padding: 3px 8px;
}
.seal.open {
  color: var(--tell);
  border-color: var(--tell);
}

@media (max-width: 860px) {
  .workbench {
    grid-template-columns: 1fr;
  }
  .rail {
    position: static;
  }
}
</style>
