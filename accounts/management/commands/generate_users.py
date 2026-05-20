from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from accounts.models import AccountGenerationBatch, GeneratedAccountRecord
from accounts.user_utils import generate_random_username, generate_random_password


class Command(BaseCommand):
    help = '批量生成客户学习账号（随机用户名与密码），可选写入留档'

    def add_arguments(self, parser):
        parser.add_argument('-n', '--count', type=int, default=1, help='生成数量')
        parser.add_argument('-p', '--prefix', type=str, default='sf', help='用户名前缀')
        parser.add_argument('-l', '--length', type=int, default=10, help='密码长度')
        parser.add_argument('--note', type=str, default='', help='批次备注')
        parser.add_argument('--archive', action='store_true', help='写入数据库留档')

    def handle(self, *args, **options):
        count = options['count']
        prefix = options['prefix']
        length = options['length']
        note = options.get('note') or ''
        archive = options['archive']

        batch = None
        if archive:
            batch = AccountGenerationBatch.objects.create(
                count=0,
                prefix=prefix,
                password_length=length,
                note=note or '命令行生成',
            )

        self.stdout.write(self.style.SUCCESS(f'生成 {count} 个账号：'))
        records = []
        for i in range(count):
            username = generate_random_username(prefix=prefix)
            password = generate_random_password(length=length)
            user = User.objects.create_user(username=username, email='', password=password)
            self.stdout.write(f'  {i + 1}. 用户名: {username}  密码: {password}')
            if batch:
                records.append(GeneratedAccountRecord(
                    batch=batch, username=username, password=password, user=user
                ))

        if batch:
            GeneratedAccountRecord.objects.bulk_create(records)
            batch.count = count
            batch.save(update_fields=['count'])
            self.stdout.write(self.style.SUCCESS(f'已留档，批次号: {batch.batch_id}'))

        self.stdout.write(self.style.SUCCESS('完成。请将账号密码分发给客户。'))
