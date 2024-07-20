from django.db import models
from mentor.models import validate_image_size, FileExtensionValidator

# Create your models here.
class AboutImage(models.Model):
    image_name = models.CharField(max_length=50)
    image = models.ImageField(
        upload_to='uploads/about/', 
        null=False, 
        blank=False,
        default='uploads/01_2.jpg',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg'], message='Only JPEG/JPG files are allowed.'),
            validate_image_size,
        ]
    )
    def __str__(self):
        return self.image_name

class Contact(models.Model):
    name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=10)
    message = models.TextField()
    
    def __str__(self):
        return self.name

    