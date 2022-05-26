from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    viewsets, mixins, status, exceptions, filters)
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated

from cookbook.models import (
    Recipe, User, Tag, Cart, Favourite, Follow, Ingredient,
    RecipeIngredient)
from .filters import RecipeFilter
from .permissions import AuthorOrReadOnly
from .paginations import CustomPagination
from .serializers import (
    UserSerializer, PasswordSerializer, GetTokenSerializer,
    TagSerializer, WriteRecipeSerializer, CartSerializer,
    FollowSerializer, IngredientSerializer, ReadRecipeSerializer)


class CreateListRetrieveViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    pass


class UserViewSet(CreateListRetrieveViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination

    @action(detail=False,
            methods=['GET', ],
            url_path='me',
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False,
            methods=['POST', ],
            url_path='set_password',
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        password = serializer.validated_data.get('current_password')
        new_password = serializer.validated_data.get('new_password')
        if user.password != password:
            msg = ('Неверный пароль.')
            raise exceptions.ValidationError(msg)
        user.password = new_password
        user.save(update_fields=['password'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['GET', ],
            url_path='subscriptions',
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        follows = request.user.follower.all()
        page = self.paginate_queryset(follows)
        if page is not None:
            serializer = FollowSerializer(
                page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)
        serializer = FollowSerializer(
            follows, many=True, context=self.get_serializer_context())
        return Response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    # serializer_class = WriteRecipeSerializer
    permission_classes = (AuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return ReadRecipeSerializer
        return WriteRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False,
            methods=['GET', ],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        filename = 'test.txt'
        carts = request.user.cart.all()
        dict_amount = {}
        dict_unit = {}
        for cart in carts:
            recipe = cart.recipe
            for ingredient in recipe.ingredients.all():
                dict_unit[ingredient.name] = ingredient.measurement_unit
                amount_storage = get_object_or_404(
                    RecipeIngredient, recipe=recipe, ingredient=ingredient)
                amount = amount_storage.amount
                existing = dict_amount.get(ingredient.name)
                if existing:
                    dict_amount[ingredient.name] = (
                        int(amount) + int(existing))
                else:
                    dict_amount[ingredient.name] = int(amount)
        str_final = ''
        for i in range(0, len(dict_amount)):
            new_str = (
                str(list(dict_amount.keys())[i]) + ' (' +
                str(dict_unit[list(dict_amount.keys())[i]]) +
                ') - ' + str(list(dict_amount.values())[i]))
            str_final = str_final + new_str + '\n'
        response = HttpResponse(
            str_final, content_type='text/plain; charset=UTF-8')
        response['Content-Disposition'] = (
            'attachment; filename={0}'.format(filename))
        return response


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class CartView(APIView):
    def post(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('pk')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        user = request.user
        action = self.kwargs.get('action')
        if action == 'shopping_cart':
            try:
                Cart.objects.create(recipe=recipe, user=user)
            except Exception:
                response = {'errors': 'Этот объект уже добавлен'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        elif action == 'favorite':
            try:
                Favourite.objects.create(recipe=recipe, user=user)
            except Exception:
                response = {'errors': 'Этот объект уже добавлен'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = CartSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        action = self.kwargs.get('action')
        if action == 'shopping_cart':
            object = request.user.cart.all()
        elif action == 'favorite':
            object = request.user.favourite.all()
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        recipe_id = self.kwargs.get('pk')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        object.filter(recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowView(APIView):
    def post(self, request, *args, **kwargs):
        following_id = self.kwargs.get('pk')
        following = get_object_or_404(User, id=following_id)
        user = request.user
        try:
            follow = Follow.objects.create(user=user, following=following)
        except Exception:
            response = {'errors': 'Подписка невозможна!'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        serializer = FollowSerializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        objects = request.user.follower.all()
        following_id = self.kwargs.get('pk')
        following = get_object_or_404(User, id=following_id)
        objects.filter(following=following).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


def get_tokens_for_user(user):
    token = Token.objects.create(user=user)
    return {
        'auth_token': str(token.key),
    }


@api_view(['POST'])
@permission_classes((AllowAny,))
def get_token(request):
    serializer = GetTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(User, email=request.data.get('email'))
    if user.password == request.data.get('password'):
        return Response(
            get_tokens_for_user(user), status=status.HTTP_201_CREATED
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def delete_token(request):
    user = request.user
    user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
