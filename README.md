# SpeakFly 后端 (Django)

口语练习网站的后端 API，使用 Django + Django REST Framework + JWT。  
**数据库**：支持 MySQL（推荐）或 SQLite。**媒体文件**：图片、视频、音频存放在阿里云 OSS，数据库只存 URL。

## 环境要求

- Python 3.8+
- pip
- 使用 MySQL 时：本地安装 MySQL 或使用云数据库

## 配置（可选）

复制 `.env.example` 为 `.env`，按需填写：

```bash
cp .env.example .env
```

- **MySQL**：若配置了 `MYSQL_NAME` 等变量，将使用 MySQL；不配置则使用 SQLite。
- **阿里云 OSS**：若配置了 `OSS_ACCESS_KEY_ID` 等，可使用上传接口将文件上传到 OSS；不配置时上传接口会提示未配置，可手动在 OSS 控制台上传后把 URL 填到后台。

## 安装与运行

1. 进入项目目录并创建虚拟环境（推荐）：

```bash
cd speakFly_back_end
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. **使用 MySQL 时**：先创建数据库（如 `speakfly`），再执行迁移；使用 SQLite 可跳过建库。

```bash
python manage.py migrate
```

4. 加载初始课程数据（可选，会创建 8 条示例视频和 1 条课程详情）：

```bash
python manage.py load_initial_data
```

5. 创建管理员账号（用于登录后台并拥有「管理员」权限访问 /admin 与后台管理接口）：

```bash
python manage.py createsuperuser
```

按提示输入用户名、邮箱、密码。将该用户的 **is_staff** 设为 True 即可在前端拥有管理员权限（创建 superuser 时默认已是 staff）。

6. 启动开发服务器：

```bash
python manage.py runserver
```

默认地址：http://127.0.0.1:8000

## API 概览

- **认证**
  - `POST /api/auth/register/` — 注册（username, email, password, confirmPassword）
  - `POST /api/auth/login/` — 登录（username, password），返回 `access`(JWT)、`user`(含 isAdmin)
  - `GET /api/auth/me/` — 当前用户信息（需 Authorization: Bearer &lt;token&gt;）

- **视频课程**
  - `GET /api/videos/` — 视频列表（需登录）
  - `GET /api/videos/{id}/` — 视频详情
  - `POST /api/videos/` — 创建视频（管理员）
  - `PUT /api/videos/{id}/` — 更新视频（管理员）
  - `DELETE /api/videos/{id}/` — 删除视频（管理员）
  - `POST /api/videos/{id}/favorite/` — 切换收藏
  - `GET /api/videos/{id}/lesson/` — 该视频的课程详情
  - `GET /api/videos/next-episode/` — 下一期数（管理员）

- **课程详情**
  - `GET /api/lessons/?video_id=1` — 按 video_id 获取课程详情
  - `POST /api/lessons/` — 创建/更新课程详情（body 含 videoId, chineseText, englishText, phrases, sentences, highlightPhrases）（管理员）

- **上传到 OSS**（管理员，图片/视频/音频存 OSS，数据库只存 URL）
  - `POST /api/upload/` — multipart/form-data：`file` 必填，`type` 可选（image / video / audio），返回 `{ "url": "https://..." }`

## 数据库（MySQL）

- 在 MySQL 中创建数据库（如 `CREATE DATABASE speakfly CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`）。
- 在 `.env` 中设置 `MYSQL_NAME`、`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_HOST`、`MYSQL_PORT`。
- 不设置 `MYSQL_NAME` 时，自动使用 SQLite（`db.sqlite3`）。

## 阿里云 OSS（图片/视频/音频）

- 所有媒体文件上传到 OSS，数据库只存 URL（`Video.thumbnail`、`Video.video_url`，以及课程详情 JSON 中的音频 URL 等）。
- 在 `.env` 中配置 `OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`、`OSS_BUCKET_NAME`、`OSS_ENDPOINT`；可选 `OSS_BUCKET_DOMAIN`（自定义域名）、`OSS_UPLOAD_DIR`（存储目录前缀）。
- 管理员可通过 `POST /api/upload/` 上传文件，接口返回 URL，将 URL 填入课程缩略图、视频 URL 或短语/句子中的音频字段即可。
- 若未配置 OSS，上传接口会返回错误，可改为在 OSS 控制台上传后手动填写 URL。

## 前端对接

前端默认请求 `http://127.0.0.1:8000`。若后端地址不同，可在前端项目根目录创建 `.env` 并设置：

```
VITE_API_URL=http://你的后端地址
```

然后重启前端开发服务器。
