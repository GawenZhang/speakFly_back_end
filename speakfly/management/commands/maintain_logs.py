from django.conf import settings
from django.core.management.base import BaseCommand

from speakfly.log_handlers import run_log_maintenance


class Command(BaseCommand):
    help = '维护日志：7 天前压缩为 .gz，30 天前删除（UTC）'

    def handle(self, *args, **options):
        log_dir = settings.LOG_DIR
        run_log_maintenance(
            log_dir,
            retention_days=settings.LOG_RETENTION_DAYS,
            compress_after_days=settings.LOG_COMPRESS_AFTER_DAYS,
        )
        self.stdout.write(self.style.SUCCESS(f'Log maintenance done: {log_dir}'))
