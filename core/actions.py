import cgi
import io
import os
from poweradmin.actions import label_for_field, get_field_value, display_for_field, display_for_value, nvl
from django.conf import settings
from django.contrib.admin.utils import label_for_field, display_for_field, display_for_value
from django.db import models
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils.formats import localize
from django.utils.html import strip_tags
from xhtml2pdf.document import pisaDocument
from django.db.models import Sum


def report_action(description="Impressão", fields=None, title='', template_name='admin/report.html', field_sum=None):
    def report(modeladmin, request, queryset):
        header = []
        linhas = []
        style = []
        for field in fields:
            field_detail = field.split(':')
            field_name = field_detail[0]
            try:
                text, attr = label_for_field(
                    field_name, modeladmin.model,
                    model_admin=modeladmin,
                    return_attr=True
                )
            except:
                if '__' in field_name:
                    text = field_name.split('__')[1]
                else:
                    text = field_name

            if len(fields) < 3:
                align = "text-align: %s;" % 'left'
                width = '"width: %s; %s"' % ('400px', align)
            else:
                align = "text-align: %s;" % (field_detail[2] if len(field_detail) > 2 else 'center')
                width = '"width: %s; %s"' % (field_detail[1] if len(field_detail) > 1 else '300px', align)

            style.append(width)

            header.append('<th class="border-top border-bottom" style=%s><b>%s</b></th>' % (width, text))

        for obj in queryset:
            line = ''
            fieldno = 0
            for field in fields:
                field_detail = field.split(':')
                field_name = field_detail[0]
                f, attr, value = get_field_value(field_name, obj, modeladmin)
                # print(f, attr, value)
                if f is None or f.auto_created:
                    boolean = getattr(attr, 'boolean', False)
                    result_repr = display_for_value(value, boolean)
                else:
                    if hasattr(f, 'rel') and isinstance(f.rel, models.ManyToOneRel):
                        field_val = getattr(obj, f.name)
                        if field_val is None:
                            result_repr = ' '
                        else:
                            result_repr = field_val
                    else:
                        result_repr = display_for_field(value, f, None)
                result_repr = nvl(strip_tags(result_repr), ' ')
                line += '<td style=%s>%s</td>' % (style[fieldno], result_repr)
                fieldno += 1
            linhas.append(line)
        # print(linhas)
            
        template = get_template(template_name)
        context = {
            'title': title, 
            'header': header, 
            'linhas': linhas, 
            'request': request
        }
        
        if field_sum:
            total = queryset.aggregate(total=Sum(field_sum))['total'] or 0
            total = localize(total)
            context['total'] = total
            
        html = template.render(context)
        result = io.BytesIO()
        pdf = pisaDocument(io.BytesIO(html.encode("UTF-8")), dest=result,
                           link_callback=lambda uri, rel: os.path.join(settings.MEDIA_ROOT,
                                                                       uri.replace(settings.MEDIA_URL, "")))
        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type='application/pdf')
        return HttpResponse('Erro na geração do relatório<pre>%s</pre>' % cgi.escape(html))

    report.short_description = description
    return report
