import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import uuid
import os
from datetime import datetime, timedelta
import logging

from database.postgres_db import db

logger = logging.getLogger(__name__)


class StatisticsGenerator:
    async def generate_users_chart(self):
        """График регистраций за последние 30 дней."""
        try:
            plt.figure(figsize=(12, 6))
            pool = await db.create_pool()
            dates = []
            counts = []
            async with pool.acquire() as conn:
                for i in range(30, -1, -1):
                    day_start = (datetime.now() - timedelta(days=i)).replace(hour=0, minute=0, second=0)
                    day_end = day_start + timedelta(days=1)
                    count = await conn.fetchval(
                        "SELECT COUNT(*) FROM users WHERE created_at >= $1 AND created_at < $2",
                        day_start, day_end
                    )
                    dates.append(day_start.strftime('%m-%d'))
                    counts.append(count or 0)
            plt.plot(dates, counts, 'o-', color='#FFD700', linewidth=2, markersize=6)
            plt.fill_between(dates, counts, alpha=0.3, color='#FFD700')
            plt.title('Регистрации пользователей', color='white', fontsize=14, pad=20)
            plt.xlabel('Дата', color='white')
            plt.ylabel('Новых пользователей', color='white')
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3)
            plt.style.use('dark_background')
            filename = f"chart_{uuid.uuid4().hex}.png"
            plt.tight_layout()
            plt.savefig(filename, facecolor='#1a2a3a', dpi=100)
            plt.close()
            return filename
        except Exception as e:
            logger.error(f"Ошибка генерации графика: {e}")
            return None

    async def generate_subscription_chart(self):
        """Круговая диаграмма подписок."""
        try:
            plt.figure(figsize=(10, 6))
            pool = await db.create_pool()
            async with pool.acquire() as conn:
                paid = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_paid = TRUE")
                free = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_paid = FALSE")
            labels = ['Премиум', 'Бесплатные']
            sizes = [paid or 0, free or 0]
            colors = ['#FFD700', '#4a5568']
            explode = (0.05, 0)
            plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                    autopct='%1.1f%%', shadow=True, startangle=90)
            plt.title('Распределение пользователей по подпискам', color='white', fontsize=14, pad=20)
            plt.style.use('dark_background')
            filename = f"chart_{uuid.uuid4().hex}.png"
            plt.tight_layout()
            plt.savefig(filename, facecolor='#1a2a3a', dpi=100)
            plt.close()
            return filename
        except Exception as e:
            logger.error(f"Ошибка генерации графика подписок: {e}")
            return None

    async def generate_comprehensive_report(self):
        chart_users = await self.generate_users_chart()
        chart_subs = await self.generate_subscription_chart()
        return {'users_chart': chart_users, 'subscription_chart': chart_subs}


stats_gen = StatisticsGenerator()
