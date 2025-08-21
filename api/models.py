from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Ingredient(models.Model):
    CATEGORY_CHOICES = (
        ('Vegetables', 'Vegetables'),
        ('Fruits', 'Fruits'),
        ('Seasoning', 'Seasoning'),
        ('Diary', 'Diary'),
        ('Sweets', 'Sweets'),
        ('Baking', 'Baking'),
        ('Sauces', 'Sauces'),
        ('Oils', 'Oils'),
        ('Seeds', 'Seeds'),
        ('Fluids', 'Fluids'),
    )

    name = models.CharField(max_length=30, unique=True, null=False, blank=False)
    category = models.CharField(max_length=30, null=False, blank=False, choices=CATEGORY_CHOICES)

    def __str__(self):
        return "Name: " + self.name + ", Category: " + self.category

class Recipe(models.Model):

    def validate_image_type(image):
        valid_mime_types = ['image/jpeg', 'image/png', 'image/gif', 'image/jpg']
        if hasattr(image, 'content_type'):
            mime_type = image.content_type
        elif hasattr(image, 'file') and hasattr(image.file, 'content_type'):
            mime_type = image.file.content_type
        else:
            # fallback or raise error
            raise ValidationError('Cannot determine the image MIME type.')
        if mime_type not in valid_mime_types:
            raise ValidationError('Unsupported file type.')

    CATEGORY_CHOICES = (
        ('Soups and Stews', 'Soups and Stews'),
        ('Salads', 'Salads'),
        ('Meat', 'Meat'),
        ('Side Dishes', 'Side Dishes'),
        ('Desserts', 'Desserts'),
        ('Breakfast and Brunch', 'Breakfast and Brunch'),
        ('Sauces and Condiments', 'Sauces and Condiments'),
    )

    DIFFICULTY_CHOICES = (
        ('Easy', 'Easy'),
        ('Intermediate', 'Intermediate'),
        ('Hard', 'Hard'),
    )

    title = models.CharField(max_length=30, unique=True, null=False, blank=False) # REQUIRED
    category = models.CharField(choices=CATEGORY_CHOICES, null=False, blank=False) # REQUIRED
    description = models.TextField(max_length=100, blank=False, null=True)
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient', blank=True)
    cook_time = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], blank=False, null=False) # REQUIRED
    servings = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], blank=False, null=False) # REQUIRED
    difficulty = models.CharField(choices=DIFFICULTY_CHOICES, blank=False, null=False) # REQUIRED
    image = models.ImageField(upload_to='images/', blank=False, null=False, validators=[validate_image_type])
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes') # REQUIRED
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=False) # REQUIRED
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=False) # REQUIRED

    def __str__(self):
        return self.title

    def no_of_steps(self):
        steps = Instruction.objects.filter(recipe=self)
        return len(steps)

    class Meta:
        ordering = ['-created_at']

class Instruction(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    step_number = models.PositiveIntegerField(default=1, blank=True, null=False)
    data = models.TextField(blank=False, null=False)

    def __str__(self):
        return self.data

class RecipeIngredient(models.Model):
    PREFIX_CHOICES = (
        ('', ''),
        ('g', 'g'),
        ('ml', 'ml'),
    )

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(default=1, null=False, blank=False)
    prefix = models.CharField(max_length=10, null=False, blank=True, choices=PREFIX_CHOICES)

    class Meta:
        unique_together = ('recipe', 'ingredient')
        indexes = [models.Index(fields=['recipe', 'ingredient'])]