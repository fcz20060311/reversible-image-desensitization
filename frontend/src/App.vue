<script setup lang="ts">
import { computed, ref } from "vue";
import type { UploadFile } from "element-plus";
import { base64ToBlob, desensitizeApi, restoreApi } from "./api";
import type { Item, RestoreResult } from "./api";

const activeTab = ref("desensitize");

// —— 脱敏页状态 ——
const files = ref<File[]>([]);
const items = ref<Item[]>([]);
const key = ref("");
const loading = ref(false);

// —— 还原页状态 ——
const restoreFiles = ref<File[]>([]);
const restoreKeyInput = ref("");
const restoreLoading = ref(false);
const restoreResults = ref<RestoreResult[]>([]);

const totalRegions = computed(() => items.value.reduce((s, it) => s + it.regionCount, 0));
const failedCount = computed(() => restoreResults.value.filter((r) => !r.ok).length);

// 脱敏页：文件选择
function syncFiles(fileList: UploadFile[]) {
  files.value = fileList.map((f) => f.raw).filter((f) => !!f);
}
function onChange(_f: UploadFile, list: UploadFile[]) {
  syncFiles(list);
}
function onRemove(_f: UploadFile, list: UploadFile[]) {
  syncFiles(list);
}

// 还原页：文件选择
function syncRestoreFiles(fileList: UploadFile[]) {
  restoreFiles.value = fileList.map((f) => f.raw).filter((f) => !!f);
}
function onRestoreChange(_f: UploadFile, list: UploadFile[]) {
  syncRestoreFiles(list);
}
function onRestoreRemove(_f: UploadFile, list: UploadFile[]) {
  syncRestoreFiles(list);
}

async function desensitize() {
  if (!files.value.length) return;
  loading.value = true;
  try {
    const data = await desensitizeApi(files.value);
    key.value = data.key;
    items.value = data.images.map((it) => {
      const blob = base64ToBlob(it.image_base64);
      return { filename: it.filename, regionCount: it.region_count, url: URL.createObjectURL(blob), blob };
    });
  } catch {
    alert("批量脱敏失败，请重试");
  } finally {
    loading.value = false;
  }
}

async function restore() {
  if (!restoreKeyInput.value || !restoreFiles.value.length) return;
  restoreLoading.value = true;
  try {
    const data = await restoreApi(restoreKeyInput.value, restoreFiles.value);
    restoreResults.value = data.results.map((r) => {
      if (r.ok && r.image_base64) {
        const blob = base64ToBlob(r.image_base64);
        return { filename: r.filename, ok: true, url: URL.createObjectURL(blob), error: "" };
      }
      return { filename: r.filename, ok: false, url: "", error: r.error ?? "未知错误" };
    });
  } catch {
    alert("批量还原失败，请重试");
  } finally {
    restoreLoading.value = false;
  }
}

function copyKey() {
  navigator.clipboard.writeText(key.value);
}

function downloadItem(it: Item) {
  const a = document.createElement("a");
  a.href = it.url;
  a.download = it.filename.replace(/\.[^.]+$/, "") + "_脱敏.png";
  a.click();
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

    <el-tabs v-model="activeTab" class="tabs">
      <!-- ===== 脱敏页 ===== -->
      <el-tab-pane label="脱敏 · 加密" name="desensitize">
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
            <div class="drop-title">拖入原图</div>
            <div class="drop-sub">或点击选择 · 可一次多张</div>
          </div>
        </el-upload>

        <div class="row">
          <el-button class="btn-primary" :loading="loading" :disabled="!files.length" @click="desensitize">
            批量脱敏
          </el-button>
          <span class="muted">{{ files.length ? `已选 ${files.length} 张` : "未选择文件" }}</span>
        </div>

        <div v-if="key" class="keycard">
          <div class="keycard-head">
            <span class="keycard-label">共享密钥 · SHARED KEY</span>
            <el-button class="copy-btn" text @click="copyKey">复制</el-button>
          </div>
          <div class="keycard-value">{{ key }}</div>
          <div class="keycard-note">请保存密钥并下载脱敏图，还原时需要两者</div>
        </div>

        <div v-if="items.length" class="grid">
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
              <div class="card-foot">
                <span class="seal">已封存 · {{ it.regionCount }}</span>
                <el-button class="dl-btn" text @click="downloadItem(it)">下载</el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- ===== 还原页 ===== -->
      <el-tab-pane label="还原 · 解密" name="restore">
        <el-upload
          class="dropzone"
          drag
          multiple
          :auto-upload="false"
          :on-change="onRestoreChange"
          :on-remove="onRestoreRemove"
          accept="image/*"
        >
          <div class="drop-hint">
            <div class="drop-glyph">＋</div>
            <div class="drop-title">拖入脱敏图</div>
            <div class="drop-sub">或点击选择 · 可一次多张</div>
          </div>
        </el-upload>

        <div class="row">
          <el-input v-model="restoreKeyInput" class="key-input" placeholder="输入共享密钥" clearable />
          <el-button
            class="btn-success"
            :loading="restoreLoading"
            :disabled="!restoreKeyInput || !restoreFiles.length"
            @click="restore"
          >
            批量还原
          </el-button>
          <span class="muted">{{ restoreFiles.length ? `已选 ${restoreFiles.length} 张` : "" }}</span>
        </div>

        <div v-if="restoreResults.length" class="summary">
          成功 <b class="ok">{{ restoreResults.length - failedCount }}</b> 张 · 失败
          <b class="bad">{{ failedCount }}</b> 张
        </div>

        <div v-if="restoreResults.length" class="grid">
          <div v-for="(r, i) in restoreResults" :key="i" class="card" :class="{ fail: !r.ok }">
            <div class="frame">
              <el-image v-if="r.ok" :src="r.url" fit="contain" />
              <div v-else class="fail-box">
                <div class="fail-glyph">✕</div>
                <div class="fail-text">{{ r.error }}</div>
              </div>
            </div>
            <div class="card-info">
              <div class="card-name">{{ r.filename }}</div>
              <span class="seal" :class="{ open: r.ok, bad: !r.ok }">
                {{ r.ok ? "已还原" : "还原失败" }}
              </span>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
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
  --bad: #e2574c;
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 24px 40px;
  color: var(--bone);
}

/* 顶栏 */
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0 16px;
  border-bottom: 1px solid var(--rule);
  margin-bottom: 16px;
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

/* 标签页 */
.tabs :deep(.el-tabs__item) {
  color: #6b7280;
  font-family: "JetBrains Mono", Consolas, monospace;
  letter-spacing: 1px;
}
.tabs :deep(.el-tabs__item.is-active) {
  color: var(--brass);
}
.tabs :deep(.el-tabs__active-bar) {
  background-color: var(--brass);
}
.tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: var(--rule);
}

/* 拖拽区 */
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

/* 按钮行 */
.row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
}
.muted {
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

/* 密钥卡 */
.keycard {
  background: var(--slab);
  border: 1px solid var(--rule);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 16px;
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

/* 密钥输入 */
.key-input :deep(.el-input__wrapper) {
  background: var(--slab);
  box-shadow: 0 0 0 1px var(--rule) inset;
}
.key-input :deep(.el-input__inner) {
  color: var(--bone);
}

/* 结果统计 */
.summary {
  font-size: 13px;
  color: #6b7280;
  margin: 4px 0 14px;
}
.summary .ok {
  color: var(--tell);
}
.summary .bad {
  color: var(--bad);
}

/* 图片网格 */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.card {
  background: var(--slab);
  border: 1px solid var(--rule);
  border-radius: 12px;
  overflow: hidden;
}
.card.fail {
  border-color: var(--bad);
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
.card-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.dl-btn {
  color: var(--tell);
}

/* 封存牌 */
.seal {
  display: inline-block;
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
.seal.bad {
  color: var(--bad);
  border-color: var(--bad);
}

/* 失败卡片 */
.fail-box {
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: #0d1117;
}
.fail-glyph {
  font-size: 32px;
  color: var(--bad);
}
.fail-text {
  font-size: 12px;
  color: #6b7280;
}
</style>
