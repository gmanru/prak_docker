from django.forms import ModelForm

from .models import Post, Comment, Follow


class PostForm(ModelForm):
    class Meta:
        model = Post
        labels = {
            'group': 'Группа',
            'text': 'Сообщение',
            'image': 'Картинка'
        }
        help_texts = {
            'group': 'Выберите группу',
            'text': 'Введите ссообщение',
            'image': 'Добавьте картинку'
        }
        fields = ['text', 'group', 'image']


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Добавить комментарий'}
        help_text = {'text': 'Текст комментария'}


class FollowForm(ModelForm):
    class Meta:
        model = Follow
        labels = {'user': 'Подписка на:', 'author': 'Автор записи'}
        fields = ['user']
