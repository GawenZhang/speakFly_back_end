"""
UTC 按日切分纯文本日志；7 天压缩 .gz；30 天删除；脱敏敏感字段。
"""
import gzip
import logging
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

# GDPR：日志中屏蔽密码、Token 等
_SENSITIVE_RE = re.compile(
    r'(password|passwd|token|authorization|secret|access|refresh|api[_-]?key)'
    r'(\s*[:=]\s*|\s*")([^"\s,}\]]+)',
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r'[\w.+-]+@[\w.-]+\.\w+')
_LOG_NAME_RE = re.compile(r'^speakfly-(\d{4}-\d{2}-\d{2})\.log(\.gz)?$')


def sanitize_message(text: str) -> str:
    """脱敏：不记录密码、Token、完整邮箱等敏感信息"""
    if not text:
        return text
    s = _SENSITIVE_RE.sub(r'\1\2***', str(text))
    s = _EMAIL_RE.sub('***@***', s)
    return s


class SanitizedFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    def format(self, record):
        original = (record.msg, record.args)
        try:
            if isinstance(record.msg, str):
                record.msg = sanitize_message(record.msg)
            if record.args:
                record.args = tuple(
                    sanitize_message(a) if isinstance(a, str) else a for a in record.args
                )
            return super().format(record)
        finally:
            record.msg, record.args = original


class UtcDailyFileHandler(logging.Handler):
    """每天一个 UTC 日期文件：logs/speakfly-YYYY-MM-DD.log"""

    def __init__(self, log_dir, retention_days=30, compress_after_days=7):
        super().__init__()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self.compress_after_days = compress_after_days
        self._current_date = None
        self._stream = None
        self._last_maintain = None
        self.setFormatter(SanitizedFormatter(
            fmt='%(asctime)s UTC | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        ))
        run_log_maintenance(self.log_dir, retention_days, compress_after_days)

    def _utc_date_str(self):
        return datetime.now(timezone.utc).strftime('%Y-%m-%d')

    def _open_stream(self):
        date = self._utc_date_str()
        if self._current_date == date and self._stream:
            return
        if self._stream:
            self._stream.close()
            self._stream = None
        path = self.log_dir / f'speakfly-{date}.log'
        self._stream = open(path, 'a', encoding='utf-8')
        self._current_date = date

    def _maybe_maintain(self):
        now = datetime.now(timezone.utc)
        if self._last_maintain and (now - self._last_maintain).total_seconds() < 3600:
            return
        self._last_maintain = now
        run_log_maintenance(self.log_dir, self.retention_days, self.compress_after_days)

    def emit(self, record):
        try:
            self._maybe_maintain()
            if self._current_date and self._current_date != self._utc_date_str():
                if self._stream:
                    self._stream.close()
                    self._stream = None
            self._open_stream()
            msg = self.format(record)
            self._stream.write(msg + '\n')
            self._stream.flush()
        except Exception:
            self.handleError(record)

    def close(self):
        if self._stream:
            self._stream.close()
            self._stream = None
        super().close()


def run_log_maintenance(log_dir, retention_days=30, compress_after_days=7):
    """
    - 7 天前的 .log 压缩为 .gz
    - 30 天前的文件（含 .gz）删除
    """
    log_dir = Path(log_dir)
    if not log_dir.exists():
        return
    now = datetime.now(timezone.utc)

    for path in list(log_dir.iterdir()):
        m = _LOG_NAME_RE.match(path.name)
        if not m:
            continue
        try:
            file_date = datetime.strptime(m.group(1), '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        age_days = (now - file_date).days

        if age_days >= retention_days:
            path.unlink(missing_ok=True)
            continue

        if path.suffix == '.log' and age_days >= compress_after_days:
            gz_path = path.with_suffix('.log.gz')
            if not gz_path.exists():
                with open(path, 'rb') as f_in, gzip.open(gz_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            path.unlink(missing_ok=True)
