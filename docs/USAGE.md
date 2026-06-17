# 部署和使用指南

## 快速开始

### 方式 1: 本地运行（推荐开发）

```bash
# 1. 克隆仓库
git clone https://github.com/JJY-ux/bike-brand-daily-collector.git
cd bike-brand-daily-collector

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的邮件配置
nano .env

# 5. 运行一次（测试）
python main.py once

# 6. 启动定时任务
python main.py
```

### 方式 2: Docker 部署（推荐生产）

```bash
# 1. 配置环境变量
cp .env.example docker/.env
# 编辑 docker/.env 文件

# 2. 启动容器
cd docker
docker-compose up -d

# 3. 查看日志
docker-compose logs -f bike-collector

# 4. 停止服务
docker-compose down
```

### 方式 3: 树莓派/NAS 部署

```bash
# 在树莓派上运行
# 1. SSH 连接到设备
ssh user@192.168.1.100

# 2. 克隆仓库
git clone https://github.com/JJY-ux/bike-brand-daily-collector.git
cd bike-brand-daily-collector

# 3. 安装依赖
pip3 install -r requirements.txt

# 4. 配置 systemd 服务
sudo nano /etc/systemd/system/bike-collector.service
```

## 邮件配置指南

### 使用 Gmail

```bash
# 1. 启用 2FA 并生成应用专用密码
# https://myaccount.google.com/apppasswords

# 2. 配置 .env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-specific-password
```

### 使用企业邮箱（Trinx）

```bash
# 配置 .env
SMTP_SERVER=smtp.trinx.com
SMTP_PORT=587
SMTP_USE_TLS=true
EMAIL_USER=jiajun.yuan@trinx.com
EMAIL_PASSWORD=your-password
```

### 使用 QQ 邮箱

```bash
# 1. 生成授权码
# https://mail.qq.com -> 设置 -> 账户 -> IMAP/SMTP

# 2. 配置 .env
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
EMAIL_USER=your-email@qq.com
EMAIL_PASSWORD=your-auth-code
```

## 监控品牌配置

编辑 `config/brands.json` 来添加或修改监控的品牌：

```json
{
  "brands": [
    {
      "id": "brand_id",
      "name": "品牌名称",
      "country": "国家",
      "website": "https://official-website.com",
      "news_url": "https://official-website.com/news",
      "selector": ".news-item",
      "priority": 1
    }
  ]
}
```

### CSS 选择器参考

- **新闻卡片**：`.news-item`, `.news-card`, `article`
- **标题**：`h2`, `h3`, `.title`, `.headline`
- **链接**：`a` (父元素内)
- **日期**：`.date`, `.published`, `time`, `.meta-date`
- **描述**：`p`, `.description`, `.excerpt`

## 日志管理

日志文件保存在 `logs/app.log`

```bash
# 查看实时日志
tail -f logs/app.log

# 查看最近 100 行
tail -n 100 logs/app.log

# 搜索错误
grep ERROR logs/app.log
```

## 数据库操作

```bash
# 查看数据库
sqlite3 bike_collector.db

# 查询今天的新闻
SELECT * FROM news WHERE DATE(created_at) = DATE('now');

# 查询特定品牌的新闻
SELECT * FROM news WHERE brand = 'Trek' ORDER BY created_at DESC;

# 导出数据
sqlite3 bike_collector.db ".mode csv" ".output news.csv" "SELECT * FROM news;"
```

## 故障排除

### 问题：邮件无法发送

```bash
# 1. 检查 SMTP 配置
python -c "
from email.sender import EmailSender
sender = EmailSender('smtp.example.com', 587, 'user@example.com', 'password')
# 应该看到连接成功
"

# 2. 检查防火墙
telnet smtp.example.com 587

# 3. 检查认证信息
# 重新检查 .env 中的 EMAIL_PASSWORD
```

### 问题：无法连接到网站

```bash
# 1. 检查网络连接
ping www.trekbikes.com

# 2. 检查代理设置
# 编辑 .env，设置 USE_PROXY=true

# 3. 检查 User-Agent
# config/settings.yaml 中的 user_agents 列表应该有有效的值
```

### 问题：爬虫没有采集到新闻

```bash
# 1. 运行一次测试
python main.py once

# 2. 检查日志
tail -f logs/app.log

# 3. 测试单个爬虫
python -c "
from scrapers import BrandScraperFactory
scraper = BrandScraperFactory.create_scraper('Trek', 'https://newsroom.trekbikes.com/', '.article')
items = scraper.scrape()
print(f'Found {len(items)} items')
"
```

## 高级配置

### 添加代理

```yaml
# config/settings.yaml
scraper:
  proxy_list:
    - "http://proxy1.example.com:8080"
    - "http://proxy2.example.com:8080"
```

### 自定义邮件模板

编辑 `email/templates/daily_report.html` 来自定义邮件样式

### 添加新的数据源

创建新的爬虫类：

```python
# scrapers/brand_scrapers.py

class CustomBrandScraper(BaseScraper):
    def scrape(self) -> List[Dict[str, str]]:
        # 实现采集逻辑
        pass
```

## 监控和维护

### 定期检查

- 检查日志中是否有错误
- 验证邮件是否正常发送
- 监控数据库大小

### 数据库清理

```bash
# 删除 30 天前的数据
sqlite3 bike_collector.db "
DELETE FROM news WHERE DATE(created_at) < DATE('now', '-30 days');
VACUUM;
"
```

### 更新品牌配置

```bash
# 更新品牌列表后，重启服务
docker-compose restart bike-collector
# 或
python main.py
```

## 备份和恢复

```bash
# 备份数据库
cp bike_collector.db bike_collector.db.backup

# 备份日志
tar -czf logs_backup.tar.gz logs/

# 恢复数据库
cp bike_collector.db.backup bike_collector.db
```

## 常见问题 (FAQ)

**Q: 为什么没有收到邮件？**
A: 检查 .env 配置、SMTP 服务器和认证信息。查看日志中的具体错误信息。

**Q: 如何修改采集时间？**
A: 修改 .env 中的 `SCHEDULE_TIME=HH:MM`

**Q: 支持哪些社交媒体平台？**
A: 当前支持微博、微信公众号、Instagram、Facebook、Twitter（需要 API 认证）

**Q: 数据保存多久？**
A: 默认保存 30 天，可在代码中修改 `cleanup_old_news(days=30)`

**Q: 可以同时监控多少个品牌？**
A: 无限制，但建议不超过 50 个以避免超时

## 支持

如有问题，请：
1. 查看日志文件 `logs/app.log`
2. 检查 GitHub Issues
3. 提交新 Issue 或 Pull Request

## 许可证

MIT License
