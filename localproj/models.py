from django.db import models
from mentor.models import FileExtensionValidator, validate_image_size
from mentor.models import Mentors
# Create your models here.


class Project (models.Model):
    project_name = models.TextField()
    posted_by = models.ForeignKey(Mentors, on_delete=models.CASCADE, default=36)
    LOCALITY_CHOICES = (
        ('Thiruvananthapuram','Thiruvananthapuram'),
        ('Kollam', 'Kollam'),
        ('Alappuzha', 'Alappuzha'),
        ('Pathanamthitta', 'Pathanamthitta'),
        ('Kottayam', 'Kottayam'),
        ('Idukki', 'Idukki'),
        ('Ernakulam', 'Ernakulam'),
        ('Thrissur', 'Thrissur'),
        ('Palakkad', 'Palakkad'),
        ('Malappuram', 'Malappuram'),
        ('Kozhikode', 'Kozhikode'),
        ('Wayanad', 'Wayanad'),
        ('Kannur', 'Kannur'),
        ('Kasaragod', 'Kasaragod'),
    )
    location = models.CharField(max_length = 20, choices = LOCALITY_CHOICES, null= False, blank = False)
    
    image = models.ImageField(
        upload_to='uploads/', 
        null=True, 
        blank=True, 
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg'], message='Only JPEG/JPG files are allowed.'),
            validate_image_size,
        ]
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=False)
    
    def __str__(self):
        return self.project_name
    
class Comment (models.Model):
    post = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(max_length=30, default= "")
    response = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    

class TermsAndConditions(models.Model):
    terms_and_conditions = models.TextField()
    
    def __str__(self):
        return self.terms_and_conditions