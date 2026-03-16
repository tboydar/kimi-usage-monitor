# 设置 GitHub 公开仓库

## 步骤 1: 在 GitHub 创建仓库

1. 打开 https://github.com/new
2. 填写信息:
   - **Repository name**: `kimi-usage-monitor`
   - **Description**: `A beautiful real-time terminal monitoring tool for Kimi AI usage with Rich UI`
   - **Visibility**: ✅ Public
   - **Initialize**: ❌ 不要勾选 "Add a README file"
3. 点击 **Create repository**

## 步骤 2: 推送代码到 GitHub

```bash
cd kimi-usage-monitor

# 添加远程仓库 (替换 eugene 为你的 GitHub 用户名)
git remote add origin https://github.com/eugene/kimi-usage-monitor.git

# 推送到 main 分支
git branch -M main
git push -u origin main
```

## 步骤 3: 验证

访问 `https://github.com/eugene/kimi-usage-monitor` 确认代码已推送成功。

## 步骤 4: 发布到 PyPI (可选)

### 4.1 创建 PyPI API Token

1. 访问 https://pypi.org/manage/account/token/
2. 点击 "Add API token"
3. Token name: `kimi-usage-monitor`
4. Scope: 选择项目或整个账户
5. 点击 "Create token"
6. 复制 token (格式: `pypi-...`)

### 4.2 添加 GitHub Secret

1. 访问 `https://github.com/eugene/kimi-usage-monitor/settings/secrets/actions`
2. 点击 "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Secret: 粘贴刚才复制的 PyPI token
5. 点击 "Add secret"

### 4.3 创建 Release

```bash
# 创建标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签
git push origin v1.0.0
```

GitHub Actions 会自动:
- 构建 Python 包
- 发布到 PyPI
- 创建 GitHub Release

## 完成! 🎉

你的项目现在已经：
- ✅ 托管在 GitHub 公开仓库
- ✅ 可以通过 pip 安装 (发布后)
- ✅ 有自动化 CI/CD 流程
