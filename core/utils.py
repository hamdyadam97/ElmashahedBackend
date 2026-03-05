from weasyprint import HTML
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf import settings


def get_pdf_response(request, template_path, context, filename):
    # تجهيز اللوجو بشكل موحد
    context['logo_url'] = request.build_absolute_uri(settings.STATIC_URL + 'images/logo.png')
    context['user'] = request.user

    html_string = render_to_string(template_path, context)

    # تحويل لـ PDF
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}.pdf"'
    return response