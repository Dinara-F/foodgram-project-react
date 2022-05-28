import base64

from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator

from rest_framework import serializers

from cookbook.models import (
    User, Recipe, Tag, RecipeIngredient, Favourite, Cart,
    Ingredient, Follow)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super(Base64ImageField, self).to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    is_subscribed = serializers.SerializerMethodField(
        method_name='subscription'
    )

    def subscription(self, instance):
        try:
            user = self.context['request'].user
        except Exception:
            user = instance
        author = instance
        try:
            return Follow.objects.filter(
                user=user, following=author).exists()
        except Exception:
            return False

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'password'
        ]


class PasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=150)
    current_password = serializers.CharField(max_length=150)


class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name']


class IngredientsSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(
        validators=(MinValueValidator(
                1,
                message='Количество ингредиента должно быть 1 или более.'
            ),
        )
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']
        read_only_fields = ['id', 'name', 'color', 'slug']


class TagsField(serializers.PrimaryKeyRelatedField):

    def to_representation(self, value):
        return TagSerializer(value).data


class WriteRecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
    author = AuthorSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(
        method_name='is_in_favourites', read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='is_in_cart', read_only=True)
    image = Base64ImageField(max_length=None)
    tags = TagsField(
        queryset=Tag.objects.all(),
        many=True
    )

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return IngredientsSerializer(ingredients, many=True).data

    def is_in_favourites(self, instance):
        user_id = self.context['request'].user.id
        recipe_id = instance.id
        try:
            return Favourite.objects.filter(
                user=user_id, recipe=recipe_id).exists()
        except Exception:
            return False

    def is_in_cart(self, instance):
        user_id = self.context['request'].user.id
        recipe_id = instance.id
        try:
            return Cart.objects.filter(
                user=user_id, recipe=recipe_id).exists()
        except Exception:
            return False

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time']
        read_only_fields = [
            'author', 'is_favorited', 'is_in_shopping_cart', ]

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(
                Ingredient,
                id=ingredient_item['id']
            )
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    'Ингредиент уже добавлен'
                )
            ingredient_list.append(ingredient)
            if int(ingredient_item['amount']) <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть 1 или более.'
                )
        data['ingredients'] = ingredients
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(
                Ingredient,
                id=ingredient_data.get('id')
            )
            amount = int(ingredient_data.get('amount'))
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount
            )
        for tag in tags:
            recipe.tags.add(tag)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = instance
        recipe.name = validated_data.get('name')
        recipe.text = validated_data.get('text')
        recipe.cooking_time = validated_data.get('cooking_time')
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        recipe.tags.clear()
        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(
                Ingredient,
                id=ingredient_data.get('id')
            )
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data.get('amount')
            )
        for tag in tags:
            recipe.tags.add(tag)
        recipe.save()
        return recipe


class ReadRecipeSerializer(WriteRecipeSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time']


class CartSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField(
        method_name='subscription'
    )
    recipes = serializers.SerializerMethodField(
        method_name='get_recipes'
    )
    recipe_count = serializers.IntegerField(
       source='following.recipes.count()',
       read_only=True
    )

    def get_recipes(self, instance):
        author = instance.following
        recipes = author.recipes.all()
        limit = self.context['request'].query_params.get('recipes_limit')
        if limit:
            recipes = author.recipes.all()[:int(limit)]
        return CartSerializer(recipes, many=True).data

    def subscription(self, instance):
        user = self.context['request'].user
        author = instance.following
        try:
            return Follow.objects.filter(
                user=user, following=author).exists()
        except Exception:
            return False

    class Meta:
        model = Follow
        fields = [
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'recipes', 'recipe_count'
        ]


class GetTokenSerializer(serializers.ModelSerializer):
    email = serializers.CharField(
        required=True, max_length=150
    )
    password = serializers.CharField(
        required=True, max_length=150
    )

    class Meta:
        model = User
        fields = ['email', 'password']
