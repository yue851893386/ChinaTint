# 一纸山河 ChinaTint

> 把中国涂成你的颜色。Paint China, one city at a time.

**一纸山河**（英文名 **ChinaTint**）是一个**精确到地级市**的中国地图在线填色工具：
打开网页即得全国 300+ 地级行政区地图，点选城市、自由配色，支持搜索定位、云端保存、
多人协作，并可导出带「一纸山河 + 网址」右下角水印的 PNG 分享图。

- 🎨 点选即上色：12 色预设 + 自定义取色器
- 🔍 城市检索：按名称 / adcode 搜索，回车自动定位
- ☁️ 云端项目：注册登录后配色方案在线保存、同名覆盖、反复编辑
- 🖼️ 图片导出：全国 / 单省 PNG，右下角自动附带「一纸山河 + 你的网址」水印
- 🔐 多用户隔离：每个账号只能看到自己的项目
- 🗺️ 缩放联动：缩小看省名，放大看城市名，省界淡蓝细线

> 技术栈：**Leaflet + GeoJSON + Flask + SQLite**，无构建步骤，克隆即用。

---

## 📛 命名

- **中文名「一纸山河」**：一张纸上，涂满你的山河——适合旅行打卡、市场分布、数据叙事等一切"用颜色讲中国故事"的场景。
- **英文名 ChinaTint**：Tint 即"染色"，技术圈搜索零干扰。
- 对外分享统一口径：**中文名 + 网址**，例如：
  > 一纸山河（ChinaTint）· 中国地级市地图填色工具 · https://你的网址

---

## ⚠️ 合规声明（务必阅读）

1. **地图数据来源**：本项目使用阿里云 DataV GeoAtlas 的公开 GeoJSON 数据，仅供学习与原型验证。
2. **正式对外发布地图须合规**：根据《地图管理条例》《公开地图内容表示规范》，**公开发布、出版、展示的中国地图必须使用自然资源部标准地图**（[标准地图服务](http://bzdt.ch.mnr.gov.cn/)），并依法标注审图号，确保国界、南海诸岛、台湾、藏南、钓鱼岛及其附属岛屿等表示完整无误。
3. **本工具生成的图片不应用于**新闻发布、出版物、广告、公开展览等依法需要送审的场景；使用者对生成内容的合规性自行负责。
4. 本项目为开源学习项目，作者不对任何使用后果承担责任（详见 [LICENSE](LICENSE)）。

---

## 📸 界面预览

<!-- 建议替换为实际截图：docs/screenshot.png（全国配色图 + 右侧面板，9:16 竖版最佳） -->

## 🚀 快速开始（本地运行）

### 环境要求
- Python 3.9+，现代浏览器

### 步骤

```bash
git clone https://github.com/<你的用户名>/ChinaTint.git
cd ChinaTint
pip install -r requirements.txt
python app.py          # Starting with waitress on http://0.0.0.0:5000
```
浏览器打开 `http://localhost:5000`，首次启动自动创建 `mapdata.db`。

---

## 🌐 部署到互联网

### 方式 A：Render 一键部署（免费）

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Fork 本仓库 → 登录 [Render](https://render.com) → 点上方按钮（或 New + → Web Service）
2. 构建 `pip install -r requirements.txt`、启动 `python app.py` 已写入 `render.yaml`
3. 约 2 分钟获得 `https://chinatint-xxxx.onrender.com`

> 免费版：15 分钟无访问休眠（首次唤醒约 30 秒）；磁盘临时，**重新部署清空数据库**，正式用请接 PostgreSQL。

### 方式 B：自有服务器（推荐正式使用）

```bash
pip install -r requirements.txt
nohup python app.py > app.log 2>&1 &
```
安全组放行 5000；建议 nginx 反代 + Let's Encrypt HTTPS。国内用户可选香港/新加坡地域（免备案）。

### 方式 C：临时演示

```bash
python app.py
cloudflared tunnel --url http://localhost:5000   # 得临时 https 地址
```

---

## 📣 分享物料（对外传播统一模板）

**标准一句话**（海报 / 简介 / 群公告通用）：
> **一纸山河（ChinaTint）** · 中国地级市地图填色工具 · 开源免费 · https://你的网址

**小红书笔记模板**：见仓库外《小红书推广方案》——正文不放链接，
写"GitHub 搜索 ChinaTint 或 一纸山河"，评论区置顶引导。

**导出图片**：自带右下角水印「一纸山河 + 网址」，截图转发即自带出处。

---

## 📁 目录结构

```
ChinaTint/
├── app.py            # Flask 后端：注册/登录/会话/项目增删改查
├── index.html        # 前端单页：Leaflet 地图 + 全部交互
├── requirements.txt  # flask, waitress
├── render.yaml       # Render 一键部署
├── mapdata.db        # 运行时自动生成（勿提交）
├── LICENSE           # MIT（仅覆盖源码，不含地图数据合规责任）
└── README.md
```

## 🔌 API 一览

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| GET | `/api/ping` | 健康检查 | 否 |
| POST | `/api/register` | 注册（用户名 3-32 / 密码 6-64 位） | 否 |
| POST | `/api/login` | 登录 → Bearer Token（7 天） | 否 |
| POST | `/api/logout` | 退出并作废 Token | 是 |
| GET | `/api/projects` | 我的项目列表 | 是 |
| POST | `/api/projects` | 保存（同名覆盖）`{name, colors}` | 是 |
| GET | `/api/projects/<id>` | 加载项目 | 是 |
| DELETE | `/api/projects/<id>` | 删除项目 | 是 |

`colors` 格式：`{"320500": "#5470c6", ...}`（adcode → 颜色），可直接对接业务数据。

## 🔒 安全设计

PBKDF2-SHA256 加盐哈希 · 256 位随机 Token 服务端可失效 · 全量 `user_id` 隔离。
生产建议：HTTPS、登录限流、PostgreSQL。

## 🗺️ 数据来源与致谢

行政区划边界：[阿里云 DataV GeoAtlas](https://datav.aliyun.com/portal/school/atlas/areaSelector) · 地图渲染：[Leaflet](https://leafletjs.com/)

## 📜 License

[MIT](LICENSE) — 代码可自由使用、修改、商用；**代码许可不涵盖地图数据及生成内容的合规责任**。

## 🤝 贡献

欢迎 Issues / PR：Docker 化、PostgreSQL、暗色主题、ECharts 导出……
