from django_filters import (FilterSet, NumberFilter,
                            ModelMultipleChoiceFilter)

from cookbook.models import Recipe, Tag


class RecipeFilter(FilterSet):
    is_favorited = NumberFilter(method='filter_favorited')
    is_in_shopping_cart = NumberFilter(method='filter_cart')
    author = NumberFilter(field_name='author__id')
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        # lookup_expr='in',
        queryset=Tag.objects.all()
    )

    def filter_favorited(self, queryset, name, value):
        if value == 1:
            return queryset.filter(favorited_by=self.request.user)

    def filter_cart(self, queryset, name, value):
        if value == 1:
            return queryset.filter(in_cart_of=self.request.user)

    class Meta:
        model = Recipe
        fields = [
            'is_favorited', 'is_in_shopping_cart',
            'author', 'tags'
            ]
