<script setup lang="ts">
import { ref } from "vue";
import axios from "axios";
import type { UploadFile } from "element-plus";

// 后端地址
const API = "http://127.0.0.1:8000";

const imgUrl = ref("");
const jobId = ref("");
const faceCount = ref<number | null>(null);
const encBlob = ref<Blob | null>(null);
const loading = ref(false);

async function desensitize(uploadFile: UploadFile) {
  const file = uploadFile.raw;
  if (!file) return;

  const form = new FormData();
  form.append("file", file);

  loading.value = true;
  try {
    const resp = await axios.post(`${API}/desensitize`, form, { responseType: "blob" });
    jobId.value = (resp.headers["x-job-id"] as string) ?? "";
    faceCount.value = Number(resp.headers["x-face-count"]);
    encBlob.value = resp.data as Blob;
    imgUrl.value = URL.createObjectURL(encBlob.value);
  } catch {
    alert("脱敏失败，请重试");
  } finally {
    loading.value = false;
  }
}

async function restore() {
  if (!encBlob.value || !jobId.value) return;

  const form = new FormData();
  form.append("file", encBlob.value, "enc.png");

  loading.value = true;
  try {
    const resp = await axios.post(`${API}/restore?job_id=${jobId.value}`, form, { responseType: "blob" });
    imgUrl.value = URL.createObjectURL(resp.data as Blob);
  } catch {
    alert("还原失败，job_id 可能已失效");
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="page">
    <h1>AI 可逆脱敏系统</h1>
    <p class="sub">上传照片 → 自动脱敏人脸 → 授权还原（无损）</p>

    <div class="actions">
      <el-upload :auto-upload="false" :show-file-list="false" :on-change="desensitize" accept="image/*">
        <el-button type="primary" :loading="loading">① 选择图片并脱敏</el-button>
      </el-upload>
      <el-button type="success" :disabled="!encBlob" @click="restore">② 还原</el-button>
    </div>

    <div class="box">
      <el-image v-if="imgUrl" :src="imgUrl" fit="contain" class="result" />
      <span v-else class="placeholder">图片会显示在这里</span>
    </div>

    <div class="info">
      检测到人脸：<b>{{ faceCount ?? "-" }}</b> 张<br />
      job_id：<span class="mono">{{ jobId || "-" }}</span>
    </div>
  </div>
</template>

<style scoped>
.page {
  max-width: 640px;
  margin: 48px auto;
  padding: 0 16px;
}
.sub {
  color: #9ca3af;
  font-size: 13px;
  margin: 6px 0 20px;
}
.actions {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}
.box {
  min-height: 220px;
  border: 1px dashed #d1d5db;
  border-radius: 10px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.result {
  width: 100%;
  max-height: 520px;
}
.placeholder {
  color: #c0c4cc;
  font-size: 14px;
}
.info {
  font-size: 13px;
  color: #6b7280;
  margin-top: 14px;
  line-height: 1.9;
}
.mono {
  font-family: Consolas, monospace;
  word-break: break-all;
}
</style>
