from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

# Create your models here.


class Task(models.Model):
    title = models.CharField(max_length=100)
    completed = models.BooleanField(default=False)
    posted_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )

    def is_overdue(self, dt):
        if self.due_at is None:
            return False
        return self.due_at < dt

    def rating_display(self):
        filled = '★' * self.rating
        empty = '☆' * (5 - self.rating)
        return filled + empty
