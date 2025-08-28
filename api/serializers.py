from rest_framework import serializers, status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from api.models import Recipe, Ingredient, Instruction, RecipeIngredient


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'

class InstructionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instruction
        fields = '__all__'

class RecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
    instructions = serializers.SerializerMethodField()
    author_username = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_instructions(self, obj):
        # Get the instructions related to the current recipe instance
        instructions = Instruction.objects.filter(recipe=obj)
        return InstructionSerializer(instructions, many=True, read_only=True).data

    def get_ingredients(self, obj):
        relatedIngredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(relatedIngredients, many=True, read_only=True).data

    def get_author_username(self, obj):
        return obj.author.username

class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    record_id = serializers.SerializerMethodField()
    ingredient_id = serializers.SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = ['record_id', 'ingredient_id', 'name', 'category', 'amount', 'prefix']

    def get_name(self, obj):
        return obj.ingredient.name

    def get_category(self, obj):
        return obj.ingredient.category

    def get_record_id(self, obj):
        return obj.id

    def get_ingredient_id(self, obj):
        return obj.ingredient.id

class UserSerializer(serializers.ModelSerializer):
    user_recipes = RecipeSerializer(many=True, read_only=True, source='recipes')
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'user_recipes')
        extra_kwargs = {'user_recipes': {'required': False}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        Token.objects.create(user=user)
        return user

    def update(self, instance, validated_data):
        if 'username' in validated_data:
            instance.username = validated_data.get('username', instance.username)
        if 'password' in validated_data:
            instance.set_password(validated_data.get('password', instance.password))
        if 'email' in validated_data:
            instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance