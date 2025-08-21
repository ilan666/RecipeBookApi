from django.contrib import admin
from api.models import *

admin.site.site_header = "Recipe Book Administration"
admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(Instruction)
admin.site.register(RecipeIngredient)
