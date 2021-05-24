import arabic_reshaper
import uuid
import pathlib

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from jalali_date.fields import JalaliDateField
from reportlab.pdfgen.canvas import Canvas
from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bidi.algorithm import get_display

from HPCPortal import settings
from mainapp.models import OnlinePaymentProxy, CustomUser
from pardakht.models import Payment as PardakhtPayment

from mainapp.utils import gregorian_to_jalali


class FactorForm(forms.Form):
    user = forms.ModelChoiceField(required=True, label='کاربر', queryset=CustomUser.objects.all().order_by('last_name'),
                                  empty_label='انتخاب کنید')
    start_date = JalaliDateField(required=True, label='از تاریخ', input_formats=['%Y/%m/%d'])
    end_date = JalaliDateField(required=True, label='تا تاریخ', input_formats=['%Y/%m/%d'])

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(FactorForm, self).__init__(*args, **kwargs)
        if not self.request.user.is_staff:
            self.fields['user'].widget = forms.HiddenInput()
            self.fields['user'].disabled = True
            self.fields['user'].widget.attrs.update({
                'readonly': 'readonly'
            })
            self.fields['user'].initial = self.request.user
            self.fields['user'].queryset = CustomUser.objects.filter(pk=self.request.user.pk)

    def clean_end_date(self):
        end_date = self.cleaned_data['end_date']
        if end_date > timezone.localdate(timezone.now()):
            raise ValidationError("نمیتواند در آینده باشد")
        return end_date

    def clean(self):
        data = super(FactorForm, self).clean()
        start_date, end_date = data.get('start_date'), data.get('end_date')
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError("تاریخ شروع نمیتواند از تاریخ پایان بزرگتر باشد")
        if len(self.get_payments()) == 0:
            raise ValidationError("در تاریخ مشخص شده، هیچ پرداختی نداشته اید")

    def get_payments(self):
        data = self.cleaned_data
        start_date, end_date = data.get('start_date'), data.get('end_date')
        qs = OnlinePaymentProxy.objects.filter(
            user=data['user'], state=PardakhtPayment.STATE_SUCCESS,
        )
        payments = list()
        for pay in qs:
            if start_date <= timezone.localdate(pay.created_at) <= end_date:
                payments.append(pay)
        return payments

    def get_total_payments(self):
        payments = self.get_payments()
        total = 0
        for pay in payments:
            total += pay.price
        return total * 10  # Rial

    def generate_pdf(self):
        pathlib.Path(settings.BASE_DIR + settings.MEDIA_URL + 'factors').mkdir(parents=True, exist_ok=True)
        fn = str(uuid.uuid1()) + ".pdf"
        outfile = '/home/hpc/HPCPortal/media/factors/{}'.format(fn)  # output file name
        file_path = 'media/factors/{}'.format(fn)
        template = PdfReader("/home/hpc/HPCPortal/template.pdf", decompress=False).pages[0]  # read template pdf
        template_obj = pagexobj(template)
        canvas = Canvas(outfile)
        xobj_name = makerl(canvas, template_obj)
        canvas.doForm(xobj_name)

        pdfmetrics.registerFont(
            TTFont('BNazanin', '/home/hpc/HPCPortal/mainapp/static/mainapp/fonts/B Nazanin Bold_YasDL.com.ttf'))
        canvas.setFont('BNazanin', 14)  # set font family and size to detect persian letters

        full_name = arabic_reshaper.reshape(u'{}'.format(self.cleaned_data['user'].get_full_name()))
        full_name = get_display(full_name)
        today = timezone.localdate(timezone.now())
        canvas.drawString(21, 786, gregorian_to_jalali(today).strftime("%Y/%m/%d"))  # header date
        canvas.drawString(315, 518, f'{self.get_total_payments():,}')  # total payment
        canvas.drawString(375, 498, full_name)  # full name
        canvas.drawString(180, 518, gregorian_to_jalali(self.cleaned_data['start_date']).strftime("%Y/%m/%d"))  # from
        canvas.drawString(80, 518, gregorian_to_jalali(self.cleaned_data['end_date']).strftime("%Y/%m/%d"))  # to
        canvas.save()
        return file_path
