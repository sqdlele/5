from django.contrib import admin
from .models import User, Profile, Category, Tag, News, View, WatchLater
from django.contrib.auth.admin import UserAdmin

admin.site.register(User, UserAdmin)
admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(News)
admin.site.register(View)
admin.site.register(WatchLater)
