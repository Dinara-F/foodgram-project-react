from import_export.admin import ImportExportModelAdmin
from django.contrib import admin

from .models import (Favourite, User, Ingredient, Recipe,
                     Tag, RecipeIngredient, Cart, Follow)


@admin.register(Ingredient)
class IngredientAdmin(ImportExportModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name', )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'times_added')
    list_filter = ('author', 'name', 'tags')

    def times_added(self, obj):
        favorites = Favourite.objects.filter(recipe=obj)
        return favorites.count()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_filter = ('email', 'first_name')


admin.site.register(Tag)
admin.site.register(RecipeIngredient)
admin.site.register(Favourite)
admin.site.register(Cart)
admin.site.register(Follow)
