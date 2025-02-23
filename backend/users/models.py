from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from core.constants import USERS_ORDER
from users.constants import (
    EMAIL_LENGTH,
    FIRST_NAME_LENGTH,
    LAST_NAME_LENGTH,
    PASSWORD_LENGTH,
    USERNAME_LENGTH,
)


class FoodgramUser(AbstractUser):

    first_name = models.CharField(
        blank=False,
        null=False,
        max_length=FIRST_NAME_LENGTH,
        help_text='Up to 20 symbols',
        verbose_name='Name'
    )
    last_name = models.CharField(
        blank=False,
        null=False,
        max_length=LAST_NAME_LENGTH,
        help_text='Up to 20 symbols',
        verbose_name='Second name'
    )
    username = models.CharField(
        blank=False,
        null=False,
        max_length=USERNAME_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator()],
        help_text='Up to 30 symbols',
        verbose_name='Nickname'
    )
    email = models.EmailField(
        blank=False,
        null=False,
        max_length=EMAIL_LENGTH,
        unique=True,
        help_text='Up to 40 symbols',
        verbose_name='Email',
    )
    password = models.CharField(
        blank=False,
        null=False,
        max_length=PASSWORD_LENGTH,
        help_text='Up to 200 symbols',
        verbose_name='Password'
    )
    avatar = models.ImageField(
        default='',
        upload_to='images/avatars/',
        blank=True,
        help_text='Upload PNG or JPEG files',
        verbose_name='Upload profile picture')

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'Users'
        ordering = USERS_ORDER

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name', 'username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(FoodgramUser,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Follower')
    following = models.ForeignKey(FoodgramUser,
                                  on_delete=models.CASCADE,
                                  related_name='following',
                                  verbose_name='Following')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'], name='unique_followings'
            ),
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_prevent_self_follow',
                check=~models.Q(user=models.F('following')),
            ),
        ]
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        ordering = ('following__username',)

    def __str__(self):
        return f'{self.user.username} follows {self.following.username}'
