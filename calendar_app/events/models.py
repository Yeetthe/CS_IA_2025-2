from django.db import models
import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Event(models.Model):
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='events')
    title       = models.CharField(max_length=200)
    description = models.TextField()
    date        = models.DateField()
    file        = models.FileField(upload_to='event_files/', blank=True, null=True)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.date} - {self.username}"

    def __str__(self):
        return self.title


class UserModel(AbstractUser):
    ROLE_CHOICES = [
        ('admin',   'Admin'),
        ('student', 'Student'),
        ('parent',  'Parent'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    children = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='parents',
        limit_choices_to={'role': 'student'},
        blank=True,
        help_text="Parents can be linked to one or more student users."
    )
