from django.forms import ModelForm
from transactions.models import AcountlessTransaction, Coupon


class AccountlessTransactionCreationForm(ModelForm):
    class Meta:
        model = AcountlessTransaction
        fields = (
            'buyer_name',
            'buyer_lastname',
            'phone_number',
            'email',
            'region',
            'commune',
            'address'
        )


class CouponCreationForm(ModelForm):
    class Meta:
        model = Coupon
        fields = ('name', 'code', 'discount_percentage')

    def clean_code(self):
        code = self.cleaned_data.get('code')
        coupon_query = Coupon.objects.filter(code=code)
        if coupon_query.exists():
            self.add_error(
                'code',
                'A coupon with the same code already exist.'
            )
        return code


class MassCouponCreationForm(ModelForm):
    class Meta:
        model = Coupon
        fields = ('name', 'discount_percentage')
