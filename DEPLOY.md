# 部署说明

## 文件清单
- app.py          Flask 后端（含用户/项目管理，数据存 SQLite）
- index.html      前端页面
- requirements.txt  Python 依赖
- mapdata.db      运行时自动创建，无需提交

## 方案 A：免费托管平台（Render / Railway，适合长期在线）
1. 把本目录 3 个文件推到 GitHub 仓库
2. Render：New → Web Service → 连接仓库
   - Build Command:  pip install -r requirements.txt
   - Start Command:  python app.py
3. 部署完成后会获得 https://xxx.onrender.com
   注意：免费实例 15 分钟无访问会休眠，首次访问需等待唤醒；
   且免费版磁盘是临时的，重新部署会丢数据（正式使用请换数据库）。

## 方案 B：自己的服务器（国内访问快，推荐香港地域免备案）
1. 腾讯云/阿里云购买轻量服务器（香港/新加坡地域，免备案）
2. 安装 Python3，上传三个文件：
       pip install -r requirements.txt
       python app.py
3. 后台常驻：
       nohup python app.py > app.log 2>&1 &
   或写成 systemd 服务
4. 安全组放行 5000 端口，浏览器访问 http://服务器IP:5000
5. 建议再套一层 nginx 反向代理 + 免费 Let's Encrypt HTTPS

## 方案 C：临时分享（最快，5 分钟）
1. 本机运行 python app.py
2. 下载 cloudflared（https://github.com/cloudflare/cloudflared）
3. 执行：  cloudflared tunnel --url http://localhost:5000
   会得到一个 https://xxx.trycloudflare.com 临时公网地址
   注意：网址随机、关闭终端即失效，数据仍存你本机，适合演示。

## 上线前 checklist
- [ ] 数据库：SQLite 仅适合单进程演示；多用户正式环境换 MySQL/PostgreSQL
- [ ] HTTPS：密码登录必须走 HTTPS，用 nginx + Let's Encrypt 或托管平台自带证书
- [ ] 地图合规：正式对外发布请核对自然资源部标准地图边界（南海诸岛、藏南、台湾）
- [ ] 安全：登录接口加限流/验证码，防止爆破
