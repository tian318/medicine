# 作品安装声明

本文档详细说明如何安装和运行本项目，包括环境配置、依赖安装和启动步骤。

## 项目概述

本项目是一个基于机器学习的中药材价格分析与预测系统，整合全国药材资源，提供实时行情、专业资讯与智能价格分析服务。系统采用多模型集成预测体系，结合AI智能助手，实现价格走势分析、产地分布可视化等功能，为中药材行业用户提供决策支持，助力产业数字化升级。

## 系统要求

### 前端

- Node.js：v20.19.0
- npm：v10.0+

### 后端

- Python：v3.10+
- PostgreSQL：v13.0+

## 安装步骤



### 1.后端安装

#### 1.1 创建虚拟环境

```bash
cd backend
python -m venv venv
```

#### 1.2 激活虚拟环境

- Windows：

  ```bash
  venv\Scripts\activate
  ```

- Linux/Mac：

  ```bash
  source venv/bin/activate
  ```

#### 1.3 安装依赖

```bash
pip install -r requirements.txt
```

#### 1.4 配置数据库

1. 确保PostgreSQL服务已启动

2. 创建数据库：

   ```sql
   CREATE DATABASE medicine_db;
   ```

3. 配置数据库连接信息（在后端代码中修改相关配置）

#### 1.5 启动后端服务

```bash
python api/app.py
```

后端服务默认运行在 `http://localhost:5002。

### 2. 前端安装

#### 2.1 安装依赖

```bash
cd frontend
npm install
```

#### 2.2 配置API地址

修改 `.env.development` 文件中的API地址，确保与后端服务地址一致：

```
VITE_API_BASE_URL=http://localhost:5003
```

#### 2.3 启动前端开发服务器

```bash
npm run dev
```

前端开发服务器默认运行在 `http://localhost:5003。

#### 2.4 构建生产版本

如果需要构建生产版本：

```bash
npm run build
```

构建产物将生成在 `dist` 目录中。

## 环境变量配置

### 后端环境变量

| 变量名         | 说明           | 默认值                                                |
| -------------- | -------------- | ----------------------------------------------------- |
| FLASK_APP      | Flask应用入口  | app.py                                                |
| FLASK_ENV      | 运行环境       | development                                           |
| DATABASE_URL   | 数据库连接URL  | postgresql://user:password@localhost:5432/medicine_db |
| OPENAI_API_KEY | OpenAI API密钥 | 无（需要自行配置）                                    |

### 前端环境变量

| 变量名            | 说明        | 默认值                |
| ----------------- | ----------- | --------------------- |
| VITE_API_BASE_URL | API基础地址 | http://localhost:5003 |

## 依赖说明

### 后端依赖

详见 `backend/requirements.txt` 文件。

### 前端依赖

详见 `frontend/package.json` 文件。

## 常见问题与解决方案

### 1. 后端服务启动失败

- **问题**：数据库连接失败
  **解决方案**：检查PostgreSQL服务是否启动，数据库是否创建，连接信息是否正确。

- **问题**：依赖安装失败
  **解决方案**：确保Python版本正确，尝试使用 `pip install --upgrade pip` 升级pip后再安装依赖。

### 2. 前端服务启动失败

- **问题**：依赖安装失败
  **解决方案**：确保Node.js版本正确，尝试删除 `node_modules` 目录和 `package-lock.json` 文件后重新安装依赖。

- **问题**：API请求失败
  **解决方案**：检查后端服务是否启动，API地址配置是否正确。

### 3. 功能异常

- **问题**：AI助手功能不可用
  **解决方案**：确保配置了有效的OpenAI API密钥。

- **问题**：数据显示异常
  **解决方案**：检查数据库中是否有数据，后端API是否正常响应。

## 注意事项

1. 本项目使用了多个开源库和组件，使用时请遵守各自的许可证要求。
2. 对于生产环境部署，建议使用适当的服务器配置和安全措施。
3. 定期更新依赖库以确保安全性和稳定性。
4. 如有问题，请参考相关文档或联系1482798393@qq.com。

---

_本文档将根据项目的发展和变化进行更新。_
