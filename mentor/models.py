from django.db import models
from datetime import datetime
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

def validate_image_size(value):
    filesize = value.size
    if filesize > 2 * 1024 * 1024:  # 2MB
        raise ValidationError("The maximum file size that can be uploaded is 2MB.")

def validate_phone_number(value):
    if not value.isdigit() or len(value) < 10 or len(value) > 15:
        raise ValidationError('Invalid phone number')


class Category(models.Model):
    name = models.TextField(unique=True)

    def __str__(self):
        return self.name

class Specialization(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    specialist = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.category.name} - {self.specialist}"

class Mentee(models.Model):

    mentor_name = models.CharField(max_length=100, unique = False)
    mentor_contact = models.CharField(max_length=15, default = "Contact number not found 😔")
    mentee_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    mentee_requirement = models.CharField(max_length = 500, null=True, default="Mentee has mentioned nothing")

    def __str__(self):
        return self.mentee_name




class Mentors(models.Model):
    name = models.CharField(max_length=40)
    contact = models.CharField(max_length=15, default = "")
    email = models.EmailField(max_length=100, default = None, null=True)
    qualification = models. CharField(max_length = 200, null= True)
    pub_date = models.DateTimeField("date published", default=datetime.now)
    categories = models.ManyToManyField(Category, related_name='mentors')
    specializations = models.ManyToManyField(Specialization, related_name='mentors', blank=True)
    date_of_birth = models.DateField("date of birth")
    experience = models.IntegerField("Years of Experience")
    WEEKDAY_CHOICES = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )
    start_weekday = models.CharField(max_length=10, choices=WEEKDAY_CHOICES, null=True, blank=True)
    end_weekday = models.CharField(max_length=10, choices=WEEKDAY_CHOICES, null=True, blank=True)

    def clean(self):
        # Perform validation to ensure start_weekday is before end_weekday
        if self.start_weekday and self.end_weekday:
            start_index = dict(self.WEEKDAY_CHOICES).get(self.start_weekday)
            end_index = dict(self.WEEKDAY_CHOICES).get(self.end_weekday)
            if start_index and end_index and start_index >= end_index:
                raise ValidationError("Start weekday must be before end weekday")
    time_from = models.TimeField("From", default='00:00')
    time_to = models.TimeField("To", default='00:00')
    image = models.ImageField(
        upload_to='uploads/', 
        null=False, 
        blank=False,
        default='uploads/01_2.jpg',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg'], message='Only JPEG/JPG files are allowed.'),
            validate_image_size,
        ]
    )
    instagram = models.URLField(blank = True, null = True)
    linkedin = models.URLField(blank = True, null = True)
    Facebook = models.URLField(blank = True, null = True)
    LOCALITY_CHOICES = (
        ('thiruvananthapuram','Thiruvananthapuram'),
        ('kollam', 'Kollam'),
        ('alappuzha', 'Alappuzha'),
        ('pathanamthitta', 'Pathanamthitta'),
        ('kottayam', 'Kottayam'),
        ('idukki', 'Idukki'),
        ('ernakulam', 'Ernakulam'),
        ('thrissur', 'Thrissur'),
        ('palakkad', 'Palakkad'),
        ('malappuram', 'Malappuram'),
        ('kozhikode', 'Kozhikode'),
        ('wayanad', 'Wayanad'),
        ('kannur', 'Kannur'),
        ('kasaragod', 'Kasaragod'),
    )
    locality = models.CharField(max_length = 20, choices = LOCALITY_CHOICES, null= False, blank = False)
    about = models.TextField(max_length = 500, null = True)
    status = models.BooleanField(default = False)
    premium = models.BooleanField(default=False)


    def __str__(self):
        return self.name
    
class TermsAndConditions(models.Model):
    terms_and_conditions = models.TextField()
    
    def __str__(self):
        return self.terms_and_conditions