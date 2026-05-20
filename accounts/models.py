import uuid

from django.conf import settings
from django.db import models


class AccountGenerationBatch(models.Model):
    """管理员批量生成账号的一次操作记录"""
    batch_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='account_generation_batches',
        verbose_name='操作人',
    )
    count = models.PositiveIntegerField('生成数量', default=0)
    prefix = models.CharField('用户名前缀', max_length=20, default='sf')
    password_length = models.PositiveSmallIntegerField('密码长度', default=10)
    note = models.CharField('备注', max_length=200, blank=True)
    created_at = models.DateTimeField('生成时间', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '账号生成批次'
        verbose_name_plural = '账号生成批次'

    def __str__(self):
        return f'{self.batch_id} ({self.count}个)'


class GeneratedAccountRecord(models.Model):
    """单条生成的客户账号留档（含初始密码，供管理员分发与导出）"""
    batch = models.ForeignKey(
        AccountGenerationBatch,
        on_delete=models.CASCADE,
        related_name='accounts',
        verbose_name='所属批次',
    )
    username = models.CharField('用户名', max_length=150)
    password = models.CharField('初始密码', max_length=128)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generation_record',
        verbose_name='对应用户',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        verbose_name = '生成账号记录'
        verbose_name_plural = '生成账号记录'

    def __str__(self):
        return self.username
