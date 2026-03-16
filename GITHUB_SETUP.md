# GitHub 仓库设置指南

## 创建 GitHub 仓库

### 1. 在 GitHub 上创建新仓库

1. 访问 https://github.com/new
2. 仓库名称：`kimi-usage-monitor`
3. 描述：`A beautiful real-time terminal monitoring tool for Kimi AI usage`
4. 选择 **Public**
5. 不要勾选 "Initialize this repository with a README"
6. 点击 **Create repository**

### 2. 推送本地仓库到 GitHub

```bash
# 添加远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/kimi-usage-monitor.git

# 推送代码
git branch -M main
git push -u origin main
```

### 3. 配置 GitHub Secrets（用于 PyPI 发布）

1. 访问仓库的 Settings → Secrets and variables → Actions
2. 点击 **New repository secret**
3. 添加 `PYPI_API_TOKEN` secret
   - 在 https://pypi.org/manage/account/token/ 创建 API token
   - 复制 token 并粘贴到 secret value

## 发布到 PyPI

### 手动发布

```bash
# 安装构建工具
pip install build twine

# 构建包
python -m build

# 检查包
twine check dist/*

# 上传到 PyPI (测试)
twine upload --repository testpypi dist/*

# 上传到 PyPI (正式)
twine upload dist/*
```

### 自动发布

创建 Git tag 触发自动发布：

```bash
# 创建 tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送 tag
git push origin v1.0.0
```

GitHub Actions 将自动：
1. 构建包
2. 发布到 PyPI
3. 创建 GitHub Release

## 项目链接

添加以下链接到 README：

- PyPI: https://pypi.org/project/kimi-monitor/
- Documentation: https://github.com/YOUR_USERNAME/kimi-usage-monitor#readme
- Issues: https://github.com/YOUR_USERNAME/kimi-usage-monitor/issues

## 徽章

在 README 顶部添加：

```markdown
[![PyPI version](https://badge.fury.io/py/kimi-monitor.svg)](https://badge.fury.io/py/kimi-monitor)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```
