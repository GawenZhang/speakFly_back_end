import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountGenerationBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('count', models.PositiveIntegerField(default=0, verbose_name='生成数量')),
                ('prefix', models.CharField(default='sf', max_length=20, verbose_name='用户名前缀')),
                ('password_length', models.PositiveSmallIntegerField(default=10, verbose_name='密码长度')),
                ('note', models.CharField(blank=True, max_length=200, verbose_name='备注')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='生成时间')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='account_generation_batches', to=settings.AUTH_USER_MODEL, verbose_name='操作人')),
            ],
            options={
                'verbose_name': '账号生成批次',
                'verbose_name_plural': '账号生成批次',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='GeneratedAccountRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=150, verbose_name='用户名')),
                ('password', models.CharField(max_length=128, verbose_name='初始密码')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts', to='accounts.accountgenerationbatch', verbose_name='所属批次')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='generation_record', to=settings.AUTH_USER_MODEL, verbose_name='对应用户')),
            ],
            options={
                'verbose_name': '生成账号记录',
                'verbose_name_plural': '生成账号记录',
                'ordering': ['id'],
            },
        ),
    ]
