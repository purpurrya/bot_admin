from django.contrib import admin
from .models import Product, Drink, PreOrder, Syrup

# Регистрация модели Product
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_available')  # Поля, отображаемые в списке
    list_filter = ('category', 'is_available')  # Фильтры в админке
    search_fields = ('name', 'description')  # Поля для поиска
    list_editable = ('price', 'is_available')  # Поля, которые можно редактировать прямо в списке



@admin.register(Drink)
class DrinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'category')
    list_editable = ('price', 'is_available')

@admin.register(Syrup)
class SyrupAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_available') 
    list_filter = ('category', 'is_available')  
    search_fields = ('name', 'category')  
    list_editable = ('price', 'is_available') 


# Регистрация модели PreOrder
@admin.register(PreOrder)
class PreOrderAdmin(admin.ModelAdmin):
    list_display = ('product', 'username', 'quantity', 'total_price', 'created_at')  # Поля, отображаемые в списке
    list_filter = ('created_at',)  # Фильтры по дате создания
    search_fields = ('username', 'product__name')  # Поиск по имени пользователя и названию продукта
    readonly_fields = ('created_at',)  # Поле только для чтения (дата создания)