from django.contrib import admin
from accounts.models import UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'user',
        'nickname',
        'avatar',
        'created_at',
        'updated_at',
    )


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'user_profiles'


class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'is_staff', 'date_joined')
    date_hierarchy = 'date_joined'
    inlines = (UserProfileInline,)

# de-register User
admin.site.unregister(User)
admin.site.register(User, UserAdmin)




