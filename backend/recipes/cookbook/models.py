from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator


class User(AbstractUser):
    email = models.EmailField(max_length=254, unique=True, null=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, null=True)
    last_name = models.CharField(max_length=150, null=True)
    password = models.CharField(max_length=150)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.name}'


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return f'{self.name}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes')
    name = models.CharField(max_length=200)
    image = models.FileField(upload_to='cookbook/')
    tags = models.ManyToManyField(Tag, related_name='recipe')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient')
    text = models.TextField()
    cooking_time = models.IntegerField(
        validators=[MinValueValidator(1), ])
    favorited_by = models.ManyToManyField(
        User, through='Favourite', related_name='favorites')
    in_cart_of = models.ManyToManyField(
        User, through='Cart', related_name='shopping')
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.name}'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_following'),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='no_self_follow'
            )
        )

    def __str__(self):
        return f'{self.user} is following {self.following}'


class Favourite(models.Model):
    user = models.ForeignKey(
        User,
        related_name='favourite',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='follower',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favourites'),
        )

    def __str__(self):
        return f'{self.user} has added {self.recipe} into favorites'


class Cart(models.Model):
    user = models.ForeignKey(
        User,
        related_name='cart',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='customer',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping'),
        )

    def __str__(self):
        return f'{self.recipe} is in cart of {self.user}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.IntegerField()

    def __str__(self):
        return f'{self.ingredient} in {self.recipe}'
