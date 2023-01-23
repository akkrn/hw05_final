from django.forms import ModelForm, forms
from django.utils.functional import empty

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["text", "group", "image"]

    def clean_subject(self):
        data = self.cleaned_data["text"]
        if data is not empty:
            raise forms.ValidationError("О чем бы вы хотели рассказать?")
            return data


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]

    def clean_subject(self):
        data = self.cleaned_data["text"]
        if data is not empty:
            raise forms.ValidationError("О чем бы вы хотели рассказать?")
            return data
