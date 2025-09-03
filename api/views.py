from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
import json
from rest_framework.views import APIView

from api.models import Recipe, Ingredient, Instruction, RecipeIngredient, Rating
from api.serializers import RecipeSerializer, IngredientSerializer, InstructionSerializer, RecipeIngredientSerializer, \
    UserSerializer, RatingSerializer


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

            if 'image' in request.data:
                recipe.image = request.data['image']
                recipe.save()

        except:
            response = {'Message': 'Recipe not found!'}
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        try:
            recipe_ingredient_records = RecipeIngredient.objects.filter(recipe=recipe)
            for record in recipe_ingredient_records:
                exists = False
                for ingredient in ingredients_data:
                    if ingredient['id'] == record.ingredient.id:
                        exists = True
                        break
                if not exists:
                    record.delete()
        except:
            response = {'Message': 'Failed to get recipe ingredient existing records!'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        for ingredient in ingredients_data:
            try:
                dbingredient = Ingredient.objects.get(id=ingredient['id'])
            except:
                response = {'Message': 'Ingredient not found!'}
                return Response(response, status=status.HTTP_404_NOT_FOUND)

            try:
                RecipeIngredient.objects.get_or_create(recipe=recipe,
                                                       ingredient=dbingredient,
                                                       amount=ingredient['amount'],
                                                       prefix=ingredient['prefix'])
            except:
                response = {'Message': 'Failed to update recipe ingredients data!'}
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

    @action(detail=True, methods=['post'], parser_classes=[JSONParser])
    def rate_recipe(self, request, pk=None):
        if 'stars' in request.data:
            recipe = Recipe.objects.get(id=pk)
            stars = request.data['stars']
            user = request.user

            try:
                rating = Rating.objects.get(user=user.id, recipe=recipe.id)  # Trying to get existing rating object
                rating.stars = stars  # Updating stars field
                rating.save()
                serializer = RatingSerializer(rating, many=False)  # Serialize what to display
                response = {'Message': 'Rating updated', 'Result': serializer.data}
                return Response(response, status=status.HTTP_200_OK)
            except:
                newRating = Rating.objects.create(recipe=recipe, user=user, stars=stars)  # Rating class object creation
                serializer = RatingSerializer(newRating, many=False)
                response = {'Message': 'Created new rating', 'result': serializer.data}
                return Response(response, status=status.HTTP_200_OK)
        else:
            response = {'message': 'You need to provide stars'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def destroy(self, request, *args, **kwargs):
        ingredient = self.get_object()

        try:
            records = RecipeIngredient.objects.filter(ingredient=ingredient)
            if records.exists() > 0:
                response = {'Message': 'Ingredient is in use! Can not delete!'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            else:
                ingredient.delete()
                response = {'Message': 'Ingredient deleted!'}
                return Response(response, status=status.HTTP_204_NO_CONTENT)
        except:
            response = {'Message': 'Could not get attached recipes ingredient records!'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

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

@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()
    def post(self, request, *args, **kwargs):
        email = request.data.get('email', None)
        try:
            user = User.objects.get(email=email)
        except:
            return Response({"Message": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

        token = get_random_string(length=32)

        # Build password reset link
        reset_link = request.build_absolute_uri(
            reverse('password-reset', kwargs={'token': token})
        )

        send_mail(
            'Password Reset Request',
            f'Click the link below to reset your password: {reset_link}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        return Response({"detail": "Password reset link sent to your email."}, status=status.HTTP_200_OK)
