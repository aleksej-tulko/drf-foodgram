from itertools import chain

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from rest_framework.authtoken.models import TokenProxy

from users.models import Subscription

User = get_user_model()


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    """
    Custom admin panel for the User model, providing additional
    functionality such as displaying the avatar image.

    Attributes:
        list_display (tuple): List of fields to display in the user list.
        list_editable (tuple): Fields that are editable directly from the list.
        search_fields (tuple): Fields used for searching users.
        fieldsets (tuple): Groups of fields to display when viewing
        or editing a user.
        add_fieldsets (tuple): Fields to display when creating a new user.
        readonly_fields (tuple): Fields that are read-only.
    """

    list_display = tuple(
        chain(
            UserAdmin.list_display,
            (
                'avatar_image',
            )
        )
    )

    list_editable = (
        'first_name',
        'last_name',
        'is_staff',
    )

    search_fields = (
        'username',
        'email',
    )

    fieldsets = (
        *UserAdmin.fieldsets,
        ('Additional Information',
         {'fields': (
             'avatar',
             'avatar_image',
         )}
         ),
    )

    readonly_fields = ('avatar_image',)

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': (
            'email',
            'first_name',
            'last_name',
            'is_staff',)}),
        ('Additional Information', {'fields': ('avatar',)}),
    )

    def avatar_image(self, obj) -> str:
        """
        Displays the avatar image for a user if available.

        Args:
            obj (User): The user instance being displayed.

        Returns:
            str: HTML for displaying the avatar image,
            or 'No Avatar' if not available.
        """
        if obj.avatar:
            return format_html(
                '<img src="{}" \
                    style="max-width: 100px; max-height: 100px;" />',
                obj.avatar.url
            )
        return 'No Avatar'

    avatar_image.short_description = 'Avatar'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """
    Custom admin panel for managing subscriptions between
    users and their followers.

    Attributes:
        list_display (tuple): List of fields to display for each subscription.
        search_fields (tuple): Fields used for searching subscriptions.
        readonly_fields (tuple): Fields that are read-only for subscription
        management.
    """

    list_display = ('user', 'following',)
    search_fields = ('user',)
    readonly_fields = ('user', 'user_avatar', 'following', 'following_avatar')

    def user_avatar(self, obj) -> str:
        """
        Displays the avatar image of the user (subscriber) in the subscription.

        Args:
            obj (Subscription): The subscription instance.

        Returns:
            str: HTML for displaying the user's avatar, or 'No Avatar'
            if not available.
        """
        if obj.user.avatar:
            return format_html(
                '<img src="{}" width="40" height="40" '
                'style="border-radius:50%;" />', obj.user.avatar.url)
        return 'No Avatar'

    user_avatar.short_description = 'Follower Avatar'

    def following_avatar(self, obj) -> str:
        """
        Displays the avatar image of the following user in the subscription.

        Args:
            obj (Subscription): The subscription instance.

        Returns:
            str: HTML for displaying the following user's avatar,
            or 'No Avatar' if not available.
        """
        if obj.following.avatar:
            return format_html(
                '<img src="{}" width="40" height="40" '
                'style="border-radius:50%;" />', obj.following.avatar.url)
        return 'No Avatar'

    following_avatar.short_description = 'Followin Avatar'

    fieldsets = (
        ('Subscription Information', {
            'fields': (
                ('user', 'user_avatar'),
                ('following', 'following_avatar'),
            ),
        }),
    )


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
