import django
import os



def run_large_pdf_build():
    os.environ.setdefault('PYTHONUNBUFFERED', '1')
    os.environ.setdefault('AWS_ACCESS_KEY_ID', 'AKIAQAT6YQCXBSKVZSH2')
    os.environ.setdefault('AWS_SECRET_ACCESS_KEY', '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')
    os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zoloto_viewer.config.settings.dev')
    django.setup()

    from zoloto_viewer.documents.models import ProjectFile
    from zoloto_viewer.viewer.models import Project

    project_uid = '2e870be7-0a4f-4c09-b3b7-b7633b9fc024'
    project = Project.objects.get(uid=project_uid)

    ProjectFile.objects.pdf_generate_file(project)


if __name__ == '__main__':
    run_large_pdf_build()
