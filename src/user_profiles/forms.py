from django.forms import ModelForm, CharField
from django.contrib.auth import get_user_model
from user_profiles.models import UserShippingAddress


class UserCreationForm(ModelForm):
    password1 = CharField()
    password2 = CharField()

    class Meta:
        model = get_user_model()
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'rut',
            'phone_number',
            'birthdate'
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error(
                'password2',
                'Passwords must match.'
            )
        return password2

    def clean_email(self):
        email = self.cleaned_data.get("email")
        user_query = get_user_model().objects.filter(
            email=email,
            email_verified=True
        )
        if user_query.exists():
            self.add_error(
                'email',
                'Email is already in use.'
            )
        return email

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserUpdateForm(ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'first_name', 'last_name')

    def save(self, commit=True):
        if 'email' in self.changed_data:
            self.instance.email_verified = False
        return super().save()


class UserShippingAddressCreationForm(ModelForm):
    user_id = CharField()

    class Meta:
        model = UserShippingAddress
        fields = ('region', 'commune', 'address')

    def clean_duplicate(self):
        user_id = self.cleaned_data.get('user_id')
        region = self.cleaned_data.get('region')
        commune = self.cleaned_data.get('commune')
        address = self.cleaned_data.get('address')
        model_query = UserShippingAddress.objects.filter(
            user_id=user_id,
            region=region,
            commune=commune,
            address=address
        )
        if model_query.exists():
            self.add_error(
                'user_id',
                'Duplicate address.'
            )

    def clean(self):
        super().clean()
        self.clean_duplicate()

    def save(self, commit=True):
        shipping_address = super(
            UserShippingAddressCreationForm, self
        ).save(commit=False)
        user = get_user_model().objects.get(
            pk=self.cleaned_data.get('user_id')
        )
        shipping_address.user = user
        if commit:
            shipping_address.save()
        return shipping_address
