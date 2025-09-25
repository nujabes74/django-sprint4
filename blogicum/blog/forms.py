from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm

from .models import Comment, Post


class ProfileEditForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ["title", "text", "category", "location", "pub_date", "image"]
        widgets = {
            "pub_date": forms.DateTimeInput(attrs={"type": "datetime-local"})
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Оставьте комментарий…'})
        }
        labels = {
            'text': ''
        }
