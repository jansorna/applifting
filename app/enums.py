from django.db.models import TextChoices


class TrendType(TextChoices):
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STAGNATING = "STAGNATING"
