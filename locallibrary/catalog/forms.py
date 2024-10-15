import datetime
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(help_text="Enter a date between now and 4 weeks (default 3).")

    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        # Check if a date is not in the past.
        if data < datetime.date.today():
            raise ValidationError(_('Invalid date - renewal in past'))

        # Check if a date is in the allowed range (+4 weeks from today).
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))

        # Remember to always return the cleaned data.
        return data

# from django import forms
# from .models import Book
#
# class BookForm(forms.ModelForm):
#     class Meta:
#         model = Book
#         fields = ['title', 'author', 'summary', 'isbn', 'genre']


# forms.py


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)


class CustomerUserCreationForm(UserCreationForm):
    # first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    # last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # now check if email is already used by another user
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email
    ''' In Django forms, the clean_<fieldname>() method is used specifically to validate individual 
    form fields automatically. For instance, clean_email() validates the email field during form 
    submission because Django looks for this naming pattern to perform field-specific validation. 
    If you use a different name, such as validate_email, Django won't automatically call it; you'll 
    need to manually call it inside the form's clean() method to ensure it runs during validation. 
    Using clean_<fieldname>() is the most straightforward and recommended approach for handling 
    custom field validations in Django forms. '''