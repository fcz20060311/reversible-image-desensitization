<script setup lang="ts">
import { ref } from "vue";
import { ElMessage } from "element-plus";
import { loginApi, registerApi, setToken } from "./api";

const emit = defineEmits<{ (e: "login-success"): void }>();

const mode = ref<"login" | "register">("login");
const username = ref("");
const password = ref("");
const nickname = ref("");
const loading = ref(false);

async function submit() {
  if (!username.value || !password.value) {
    ElMessage.warning("请输入用户名和密码");
    return;
  }
  loading.value = true;
  try {
    if (mode.value === "login") {
      const res = await loginApi(username.value, password.value);
      if (res.code === 1) {
        setToken(res.data);
        ElMessage.success("登录成功");
        emit("login-success");
      } else {
        ElMessage.error(res.msg);
      }
    } else {
      const res = await registerApi(username.value, password.value, nickname.value || undefined);
      if (res.code === 1) {
        ElMessage.success("注册成功，请登录");
        mode.value = "login";
      } else {
        ElMessage.error(res.msg);
      }
    }
  } catch {
    ElMessage.error("请求失败，请确认 Java 服务（8080）已启动");
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand">
        <span class="mark">▣</span>
        <h1>AI 可逆脱敏系统</h1>
        <p class="tagline">REVERSIBLE DESENSITIZATION</p>
      </div>

      <div class="tabs">
        <span :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</span>
        <span :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</span>
      </div>

      <div class="form">
        <el-input v-model="username" placeholder="用户名" size="large" />
        <el-input v-model="password" type="password" placeholder="密码" show-password size="large" />
        <el-input v-if="mode === 'register'" v-model="nickname" placeholder="昵称（可选）" size="large" />
        <el-button class="btn" :loading="loading" size="large" @click="submit">
          {{ mode === "login" ? "登 录" : "注 册" }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: #0b0e13;
}
.login-card {
  width: 380px;
  background: #151b24;
  border: 1px solid #26303c;
  border-radius: 14px;
  padding: 32px 28px;
}
.brand {
  text-align: center;
  margin-bottom: 24px;
}
.mark {
  display: inline-grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border: 1px solid #c8963e;
  color: #c8963e;
  font-family: "JetBrains Mono", Consolas, monospace;
  margin-bottom: 10px;
}
.brand h1 {
  font-size: 18px;
  color: #e8e4dc;
  letter-spacing: 1px;
}
.tagline {
  font-family: "JetBrains Mono", Consolas, monospace;
  font-size: 10px;
  letter-spacing: 3px;
  color: #6b7280;
  margin-top: 4px;
}
.tabs {
  display: flex;
  gap: 24px;
  border-bottom: 1px solid #26303c;
  margin-bottom: 20px;
}
.tabs span {
  padding: 8px 2px;
  color: #6b7280;
  cursor: pointer;
  font-size: 14px;
  border-bottom: 2px solid transparent;
}
.tabs span.active {
  color: #c8963e;
  border-bottom-color: #c8963e;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.btn {
  background: #c8963e;
  border: none;
  color: #14100a;
  font-weight: 600;
  margin-top: 6px;
}
.btn:hover {
  background: #d8a94f;
  color: #14100a;
}
</style>
