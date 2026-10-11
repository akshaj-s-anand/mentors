from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
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
    pub_date = models.DateTimeField("date published", default=timezone.now)
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

    # profile & booking details
    headline = models.CharField(max_length=120, blank=True, help_text='e.g. "Brand designer · 8 years"')
    languages = models.CharField(max_length=100, blank=True, default='Malayalam, English')
    SESSION_LENGTH_CHOICES = ((15, '15 minutes'), (30, '30 minutes'), (45, '45 minutes'), (60, '1 hour'))
    session_minutes = models.PositiveSmallIntegerField(choices=SESSION_LENGTH_CHOICES, default=30)
    price_per_session = models.PositiveIntegerField(
        null=True, blank=True, help_text='In rupees, paid directly to the mentor. Leave empty if free.'
    )
    free_intro = models.BooleanField(default=True, help_text='Offers a free first call')
    # met / checked in person by the Oldscool team (separate from `status`, which only publishes the profile)
    verified = models.BooleanField(default=False)

    # readable profile URL, e.g. /mentor/jijau-kore/; set once from the name so shared links keep working
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_mentor_slug(self.name, Mentors.objects.exclude(pk=self.pk))
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('mentor:mentor_details', args=[self.slug])

    @property
    def weekday_indexes(self):
        """Weekdays (0 = Monday) the mentor is available, handling ranges like Friday→Monday."""
        keys = [key for key, _ in self.WEEKDAY_CHOICES]
        if self.start_weekday not in keys or self.end_weekday not in keys:
            return []
        start, end = keys.index(self.start_weekday), keys.index(self.end_weekday)
        if start <= end:
            return list(range(start, end + 1))
        return list(range(start, 7)) + list(range(0, end + 1))

    @property
    def has_schedule(self):
        """True when weekdays and hours allow at least one bookable slot."""
        if not self.weekday_indexes or not self.time_from or not self.time_to:
            return False
        minutes = (self.time_to.hour * 60 + self.time_to.minute) - (self.time_from.hour * 60 + self.time_from.minute)
        return minutes >= self.session_minutes

    @property
    def whatsapp_number(self):
        return whatsapp_number(self.contact)

    @property
    def language_list(self):
        return [lang.strip() for lang in (self.languages or '').split(',') if lang.strip()]


# path segments under /mentor/ that a mentor slug must never take over
RESERVED_SLUGS = {'create', 'skills', 'mentors'}


def unique_mentor_slug(name, others):
    """'Jijau Kore' -> 'jijau-kore', or 'jijau-kore-2' if taken. `others` is the queryset to check against."""
    base = slugify(name)[:50].strip('-') or 'mentor'
    if base in RESERVED_SLUGS:
        base = f'{base}-mentor'
    slug, n = base, 2
    while others.filter(slug=slug).exists():
        slug, n = f'{base}-{n}', n + 1
    return slug


def whatsapp_number(phone):
    """Digits for a wa.me link; bare 10-digit numbers are treated as Indian (+91)."""
    digits = ''.join(ch for ch in (phone or '') if ch.isdigit())
    if len(digits) == 10:
        return '91' + digits
    return digits if len(digits) > 10 else ''
    
class TermsAndConditions(models.Model):
    terms_and_conditions = models.TextField()
    
    def __str__(self):
        return self.terms_and_conditions