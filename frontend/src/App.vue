<script setup lang="ts">
import { ref } from "vue";
import axios from "axios";
import type { UploadFile } from "element-plus";

const API = "http://127.0.0.1:8000";

const originalUrl = ref("");
const resultUrl = ref("");
const resultLabel = ref("脱敏图");
const jobId = ref("");
const regionCount = ref<number | null>(null);
const encBlob = ref<Blob | null>(null);
const loading = ref(false);

async function desensitize(uploadFile: UploadFile) {
  const file = uploadFile.raw;
  if (!file) return;
  originalUrl.value = URL.createObjectURL(file);

  const form = new FormData();
  form.append("file", file);
  loading.value = true;
  try {
    const resp = await axios.post(`${API}/desensitize`, form, { responseType: "blob" });
    jobId.value = (resp.headers["x-job-id"] as string) ?? "";
    regionCount.value = Number(resp.headers["x-region-count"]);
    encBlob.value = resp.data as Blob;
    resultUrl.value = URL.createObjectURL(encBlob.value);
    resultLabel.value = "脱敏图";
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
    resultUrl.value = URL.createObjectURL(resp.data as Blob);
    resultLabel.value = "还原图";
  } catch {
    alert("还原失败，job_id 可能已失效");
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="page">
    <header class="header">
      <h1>AI 可逆脱敏系统</h1>
      <p class="sub">上传照片 → 自动脱敏敏感信息 → 授权无损还原</p>
    </header>

    <el-upload
      class="dropzone"
      drag
      :auto-upload="false"
      :show-file-list="false"
      :on-change="desensitize"
      accept="image/*"
    >
      <div class="drop-hint">
        <div class="drop-title">把照片拖到这里</div>
        <div class="drop-sub">或点击选择文件（支持 jpg / png）</div>
      </div>
    </el-upload>

    <div class="compare">
      <div class="panel">
        <div class="panel-title">原图</div>
        <div class="panel-body">
          <el-image v-if="originalUrl" :src="originalUrl" fit="contain" />
          <span v-else class="placeholder">—</span>
        </div>
      </div>
      <div class="panel">
        <div class="panel-title">{{ resultLabel }}</div>
        <div class="panel-body">
          <el-image v-if="resultUrl" :src="resultUrl" fit="contain" />
          <span v-else class="placeholder">—</span>
        </div>
      </div>
    </div>

    <footer class="footer">
      <div class="meta">
        <span
          >检测到 <b>{{ regionCount ?? "-" }}</b> 个敏感区域</span
        >
        <el-button type="success" :disabled="!encBlob" :loading="loading" @click="restore"> 授权还原 </el-button>
      </div>
      <div class="jobid">
        job_id:<span class="mono">{{ jobId || "-" }}</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.page {
  max-width: 900px;
  margin: 40px auto;
  padding: 0 20px;
}
.header {
  margin-bottom: 24px;
}
.header h1 {
  font-size: 26px;
  font-weight: 700;
  color: #1f2937;
  letter-spacing: -0.5px;
}
.sub {
  color: #6b7280;
  font-size: 14px;
  margin-top: 6px;
}
.dropzone :deep(.el-upload-dragger) {
  border: 2px dashed #c7d0e0;
  border-radius: 12px;
  background: #fff;
  padding: 32px;
}
.drop-title {
  font-size: 16px;
  color: #2743c9;
  font-weight: 600;
}
.drop-sub {
  font-size: 13px;
  color: #9ca3af;
  margin-top: 6px;
}
.compare {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin: 20px 0;
}
.panel {
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}
.panel-title {
  font-size: 13px;
  color: #6b7280;
  padding: 12px 16px;
  border-bottom: 1px solid #eef0f4;
  background: #fafbfd;
}
.panel-body {
  min-height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
}
.panel-body :deep(.el-image) {
  width: 100%;
  max-height: 480px;
}
.placeholder {
  color: #c0c4cc;
  font-size: 20px;
}
.footer {
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
}
.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #374151;
}
.meta b {
  color: #d97706;
  font-size: 16px;
}
.jobid {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 10px;
}
.mono {
  font-family: "JetBrains Mono", Consolas, monospace;
  color: #2743c9;
  word-break: break-all;
}
</style>
