"""
流水导入 API
"""
import os
import tempfile
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from apps.imports.services import ImportService
from apps.imports.models import ImportLog


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def import_file(request):
    """单文件导入"""
    uploaded = request.FILES.get('file')
    if not uploaded:
        return Response({'error': '未上传文件'}, status=status.HTTP_400_BAD_REQUEST)

    # 保存到临时文件
    suffix = os.path.splitext(uploaded.name)[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        for chunk in uploaded.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        source_hint = request.data.get('source')
        service = ImportService()
        result = service.import_file(tmp_path, uploaded.name, source_hint)
        return Response(result)
    finally:
        os.unlink(tmp_path)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def import_batch(request):
    """批量多文件导入"""
    files = request.FILES.getlist('files')
    if not files:
        return Response({'error': '未上传文件'}, status=status.HTTP_400_BAD_REQUEST)

    all_results = []
    service = ImportService()

    for uploaded in files:
        suffix = os.path.splitext(uploaded.name)[1]
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            for chunk in uploaded.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            result = service.import_file(tmp_path, uploaded.name)
            all_results.append({
                'filename': uploaded.name,
                **result,
            })
        finally:
            os.unlink(tmp_path)

    # 汇总
    total_imported = sum(r.get('imported_rows', 0) for r in all_results)
    total_skipped = sum(r.get('skipped_rows', 0) for r in all_results)
    total_errors = sum(r.get('error_rows', 0) for r in all_results)

    return Response({
        'files': all_results,
        'summary': {
            'total_files': len(files),
            'total_imported': total_imported,
            'total_skipped': total_skipped,
            'total_errors': total_errors,
        },
    })


@api_view(['GET'])
def import_history(request):
    """导入历史列表"""
    logs = ImportLog.objects.all()[:50]
    data = []
    for log in logs:
        data.append({
            'id': log.id,
            'source': log.source,
            'source_file': log.source_file,
            'file_size': log.file_size,
            'total_rows': log.total_rows,
            'imported_rows': log.imported_rows,
            'skipped_rows': log.skipped_rows,
            'error_rows': log.error_rows,
            'error_detail': log.error_detail,
            'status': log.status,
            'created_at': log.created_at.isoformat(),
        })
    return Response(data)
