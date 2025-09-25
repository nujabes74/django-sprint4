from django.contrib import admin

from .models import Category, Location, Post


admin.site.empty_value_display = 'Не задано'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author',
                    'is_published', 'created_at')
    list_editable = ('is_published', 'category')
    list_filter = ('is_published', 'category', 'author')
    search_fields = ('title', 'category')
    ordering = ('created_at',)
    raw_id_fields = ('author', 'category', 'location')


admin.site.register(Category)
admin.site.register(Location)
