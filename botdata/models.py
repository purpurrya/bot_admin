from django.db import models

class Product(models.Model):
    # Основные поля
    name = models.CharField(max_length=200, verbose_name="Название продукта")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    category = models.CharField(max_length=100, verbose_name="Категория")
    is_available = models.BooleanField(default=True, verbose_name="Доступен")
    path = models.CharField(max_length=500, blank=True, null=True, verbose_name="Пути к фото")
    composition = models.TextField(blank=True, null=True, verbose_name="Состав продукта")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

class Drink(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название напитка")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    category = models.CharField(max_length=100, verbose_name="Категория")
    is_available = models.BooleanField(default=True, verbose_name="Доступен")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Напиток"
        verbose_name_plural = "Напитки"


class Drinks(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название сиропа")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    category = models.CharField(max_length=100, verbose_name="Категория")
    is_available = models.BooleanField(default=True, verbose_name="Доступен")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Напиток"
        verbose_name_plural = "Напитки"

class Syrup(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название сиропа")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    category = models.CharField(max_length=100, verbose_name="Категория")
    is_available = models.BooleanField(default=True, verbose_name="Доступен")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Сироп"
        verbose_name_plural = "Сиропы"


class PreOrder(models.Model):
    # Связь с продуктом
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Продукт")

    # Информация о пользователе
    user_id = models.IntegerField(verbose_name="ID пользователя")
    username = models.CharField(max_length=100, blank=True, null=True, verbose_name="Имя пользователя")

    # Информация о заказе
    quantity = models.IntegerField(default=1, verbose_name="Количество")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая стоимость")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Заказ {self.id} от {self.username}"

    class Meta:
        verbose_name = "Предзаказ"
        verbose_name_plural = "Предзаказы"