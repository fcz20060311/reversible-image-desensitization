import axios from "axios";

export const API = "http://127.0.0.1:8000";

// 一张脱敏结果（前端展示用）
export interface Item {
  filename: string;
  regionCount: number;
  url: string;
  blob: Blob;
}

// 一张还原结果
export interface RestoreResult {
  filename: string;
  ok: boolean;
  url: string;
  error: string;
}

// base64 → Blob（图片字节）
export function base64ToBlob(b64: string): Blob {
  const chars = atob(b64);
  const bytes = new Uint8Array(chars.length);
  for (let i = 0; i < chars.length; i++) bytes[i] = chars.charCodeAt(i);
  return new Blob([bytes], { type: "image/png" });
}

// 批量脱敏：返回 { key, images }
export async function desensitizeApi(files: File[]) {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const resp = await axios.post(`${API}/batch_desensitize`, form);
  return resp.data as {
    key: string;
    images: { filename: string; region_count: number; image_base64: string }[];
  };
}

// 批量还原：返回 { results }
export async function restoreApi(key: string, files: File[]) {
  const form = new FormData();
  form.append("key", key);
  files.forEach((f) => form.append("files", f));
  const resp = await axios.post(`${API}/batch_restore`, form);
  return resp.data as {
    results: { filename: string; ok: boolean; image_base64?: string; error?: string }[];
  };
}
