from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
import json

from api.models import Recipe, Ingredient, Instruction, RecipeIngredient
from api.serializers import RecipeSerializer, IngredientSerializer, InstructionSerializer, RecipeIngredientSerializer, \
    UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    authentication_classes = ()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        authentication_classes=[TokenAuthentication]
    )
    def get_user(self, request):
        user = request.user
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        if 'ingredients' not in request.data:
            response = {'Message': 'Missing ingredients array data!'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        if 'instructions' not in request.data:
            response = {'Message': 'Missing instructions array data!'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        ingredients_data = json.loads(request.data.get('ingredients', '[]'))
        instructions_data = json.loads(request.data.get('instructions', '[]'))

        recipe = Recipe.objects.create(
            title=request.data['title'],
            description=request.data['description'],
            category=request.data['category'],
            cook_time=request.data['cook_time'],
            image=request.data['image'],
            difficulty=request.data['difficulty'],
            author=request.user,
            servings=request.data['servings'],
        )

        for ingredient in ingredients_data:
            try:
                dbingredient = Ingredient.objects.get(id=ingredient['id'])
            except:
                response = {'Message': 'Ingredient not found!'}
                return Response(response, status=status.HTTP_404_NOT_FOUND)

            try:
                RecipeIngredient.objects.create(recipe=recipe, ingredient=dbingredient, amount=ingredient['amount'], prefix=ingredient['prefix'])
            except:
                response = {'Message': 'Could not add ingredient to recipe!'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        for instruction in instructions_data:
            stepNum = instruction['step_number']
            dataText = instruction['data']

            if not dataText or not stepNum:
                response = {'Message': 'Missing instruction data!'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            try:
                Instruction.objects.create(recipe=recipe, step_number=stepNum, data=dataText)
            except:
                response = {'Message': 'Failed to add instruction!'}
                return Response(response, status=status.HTTP_404_NOT_FOUND)

        serializer = RecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        if 'ingredients' not in request.data:
            response = {'Message': 'Missing ingredients array data!'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        if 'instructions' not in request.data:
            response = {'Message': 'Missing instructions array data!'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        ingredients_data = json.loads(request.data.get('ingredients', '[]'))
        instructions_data = json.loads(request.data.get('instructions', '[]'))

        try:
            recipe = Recipe.objects.get(id=kwargs['pk'])
        except:
            response = {'Message': 'Recipe not found!'}
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        for ingredient in ingredients_data:
            try:
                dbingredient = Ingredient.objects.get(id=ingredient['id'])
                RecipeIngredient.objects.get_or_create(recipe=recipe,
                                                       ingredient=dbingredient,
                                                       amount=ingredient['amount'],
                                                       prefix=ingredient['prefix'])
            except:
                response = {'Message': 'Failed to update recipe data!'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        for instruction in instructions_data:
            stepNum = instruction['step_number']
            dataText = instruction['data']

            if not dataText or not stepNum:
                response = {'Message': 'Missing instruction data!'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            try:
                record, created = Instruction.objects.get_or_create(recipe=recipe, step_number=stepNum, defaults={'data': dataText})
                if not created:
                    record.data = dataText
                    record.save()
            except:
                response = {'Message': 'Failed to add instruction!'}
                return Response(response, status=status.HTTP_404_NOT_FOUND)

        serializer = RecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

class InstructionViewSet(viewsets.ModelViewSet):
    queryset = Instruction.objects.all()
    serializer_class = InstructionSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

class RecipeIngredientViewSet(viewsets.ModelViewSet):
    queryset = RecipeIngredient.objects.all()
    serializer_class = RecipeIngredientSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)