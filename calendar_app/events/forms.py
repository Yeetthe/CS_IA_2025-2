from django import forms
from .models import Event, UserModel
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
User = get_user_model()


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'date', 'description', 'file']


class AdminCloneEventForm(forms.Form):
    student_username = forms.CharField(
        max_length=150,
        help_text="Enter the student's username to clone this event to."
    )


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'role']


class AssignChildForm(forms.Form):
    child_username = forms.CharField(label="Student Username")

    def clean_child_username(self):
        username = self.cleaned_data['child_username']
        try:
            user = User.objects.get(username=username)
            if user.role != 'student':
                raise forms.ValidationError("User is not a student.")
            return user
        except User.DoesNotExist:
            raise forms.ValidationError("No such student exists.")
