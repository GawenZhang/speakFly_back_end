from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font


def build_accounts_excel(queryset):
    """
    将 GeneratedAccountRecord queryset 导出为 xlsx 字节流。
    queryset 需 select_related('batch', 'batch__created_by')
    """
    wb = Workbook()
    ws = wb.active
    ws.title = '客户账号'

    headers = ['序号', '批次编号', '生成时间', '操作人', '用户名', '初始密码', '备注']
    header_font = Font(bold=True)
    for col, title in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=title)
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    for idx, record in enumerate(queryset, 1):
        batch = record.batch
        ws.append([
            idx,
            str(batch.batch_id),
            batch.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            batch.created_by.username if batch.created_by else '',
            record.username,
            record.password,
            batch.note or '',
        ])

    for col in ws.columns:
        max_len = 0
        column = col[0].column_letter
        for cell in col:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[column].width = min(max_len + 2, 40)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
