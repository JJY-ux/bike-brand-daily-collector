"""Main entry point for the bike brand daily collector."""

import logging
import json
import yaml
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from scrapers import NewsAggregator
from email import EmailSender
from scheduler import TaskScheduler
from database import DatabaseManager

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("./logs/app.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/settings.yaml"):
    """Load configuration from YAML file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        return {}


def load_brands(brands_path: str = "config/brands.json"):
    """Load brands configuration from JSON file."""
    try:
        with open(brands_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("brands", [])
    except Exception as e:
        logger.error(f"Failed to load brands: {str(e)}")
        return []


def generate_html_report(news_items: list, config: dict) -> str:
    """Generate HTML report from news items."""
    try:
        with open("email/templates/daily_report.html", "r", encoding="utf-8") as f:
            template = f.read()

        # Group news by brand
        news_by_brand = {}
        for item in news_items:
            brand = item.get("brand", "Unknown")
            if brand not in news_by_brand:
                news_by_brand[brand] = []
            news_by_brand[brand].append(item)

        # Generate news sections HTML
        news_sections = ""
        for brand, items in sorted(news_by_brand.items()):
            news_sections += f'<div class="brand-name">{brand}</div>\n'

            for item in items:
                title = item.get("title", "No Title")
                link = item.get("link", "#")
                date = item.get("date", "Unknown Date")
                description = item.get("description", "")

                news_sections += f"""
                <div class="news-item">
                    <h3 class="news-title">
                        <a href="{link}" target="_blank">{title}</a>
                    </h3>
                    <div class="news-meta">📅 {date}</div>
                    <p class="news-description">{description}</p>
                </div>
                """

        # Handle empty state
        empty_state = ""
        if not news_items:
            empty_state = """
            <div class="empty-state">
                <p>📭 今日暂无新闻更新</p>
            </div>
            """

        # Replace placeholders
        html_report = template.replace(
            "{date}", datetime.now().strftime("%Y年%m月%d日 %A")
        )
        html_report = html_report.replace("{total_items}", str(len(news_items)))
        html_report = html_report.replace(
            "{brands_count}", str(len(news_by_brand))
        )
        html_report = html_report.replace("{success_brands}", str(len(news_by_brand)))
        html_report = html_report.replace("{news_sections}", news_sections)
        html_report = html_report.replace("{empty_state}", empty_state)

        return html_report

    except Exception as e:
        logger.error(f"Failed to generate HTML report: {str(e)}")
        return ""


def collect_and_send():
    """Main task: collect news and send report."""
    logger.info("=" * 60)
    logger.info("Starting daily collection task")
    logger.info("=" * 60)

    try:
        # Load configuration
        config = load_config()
        brands = load_brands()

        if not brands:
            logger.error("No brands configured")
            return

        # Collect news
        logger.info(f"Collecting news from {len(brands)} brands...")
        aggregator = NewsAggregator(brands, max_workers=5)
        news_items = aggregator.collect()

        # Filter by keywords if configured
        scraper_config = config.get("scraper", {})
        content_filter = config.get("content_filter", {})

        if content_filter.get("keywords_include"):
            news_items = aggregator.filter_by_keywords(
                news_items,
                content_filter.get("keywords_include", []),
                content_filter.get("keywords_exclude", []),
            )

        logger.info(f"Collected {len(news_items)} news items")

        # Save to database
        db = DatabaseManager()
        inserted = db.insert_news(news_items)
        logger.info(f"Saved {inserted} new items to database")

        # Generate HTML report
        logger.info("Generating HTML report...")
        html_report = generate_html_report(news_items, config)

        if not html_report:
            logger.error("Failed to generate HTML report")
            return

        # Send email
        logger.info("Sending emails...")
        email_config = config.get("email", {})
        smtp_config = {
            "server": os.getenv("SMTP_SERVER", "smtp.trinx.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "user": os.getenv("EMAIL_USER", "jiajun.yuan@trinx.com"),
            "password": os.getenv("EMAIL_PASSWORD", ""),
            "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        }

        recipients = os.getenv("RECIPIENTS", "").split(",")
        recipients = [r.strip() for r in recipients if r.strip()]

        if not recipients or not smtp_config["password"]:
            logger.error("Email configuration incomplete")
            return

        sender = EmailSender(
            smtp_server=smtp_config["server"],
            smtp_port=smtp_config["port"],
            email_user=smtp_config["user"],
            email_password=smtp_config["password"],
            use_tls=smtp_config["use_tls"],
        )

        subject = email_config.get("template", {}).get("subject", "").format(
            date=datetime.now().strftime("%Y-%m-%d")
        )

        success = sender.send(
            to_addresses=recipients,
            subject=subject,
            html_content=html_report,
            from_name=email_config.get("template", {}).get(
                "from_name", "自行车品牌收集器"
            ),
        )

        if success:
            logger.info(f"Successfully sent report to {len(recipients)} recipients")
        else:
            logger.error("Failed to send report")

        logger.info("=" * 60)
        logger.info("Daily collection task completed")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error in collection task: {str(e)}", exc_info=True)


def run_scheduler():
    """Run the scheduler in background."""
    try:
        config = load_config()
        scheduler_config = config.get("scheduler", {})

        time_str = os.getenv("SCHEDULE_TIME", scheduler_config.get("time", "08:30"))
        hour, minute = map(int, time_str.split(":"))
        timezone = os.getenv("TIMEZONE", scheduler_config.get("timezone", "Asia/Shanghai"))

        scheduler = TaskScheduler(timezone=timezone)
        scheduler.add_cron_job(
            func=collect_and_send,
            hour=hour,
            minute=minute,
            job_id="daily_collection",
            name="Daily Bike Brand Collection",
        )

        scheduler.start()
        logger.info(f"Scheduler started. Task will run daily at {time_str}")

        # Keep the program running
        try:
            import time

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down scheduler...")
            scheduler.stop()

    except Exception as e:
        logger.error(f"Error in scheduler: {str(e)}", exc_info=True)


def run_once():
    """Run the collection task once (for testing)."""
    collect_and_send()


if __name__ == "__main__":
    import sys

    # Create logs directory if it doesn't exist
    Path("./logs").mkdir(exist_ok=True)

    if len(sys.argv) > 1 and sys.argv[1] == "once":
        logger.info("Running collection task once...")
        run_once()
    else:
        logger.info("Running scheduler...")
        run_scheduler()
