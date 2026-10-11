import uuid

from django.db import models
from mentor.models import FileExtensionValidator, validate_image_size
from mentor.models import Mentors, Specialization
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
    # approved by an admin and visible on the site
    status = models.BooleanField(default=False)

    budget = models.CharField(max_length=60, blank=True, help_text='e.g. "₹15,000" or "₹500/hour"')
    skills = models.ManyToManyField(Specialization, blank=True, related_name='projects')
    STAGE_OPEN, STAGE_IN_PROGRESS, STAGE_CLOSED = 'open', 'in_progress', 'closed'
    STAGE_CHOICES = ((STAGE_OPEN, 'Open for proposals'), (STAGE_IN_PROGRESS, 'In progress'), (STAGE_CLOSED, 'Closed'))
    stage = models.CharField(max_length=12, choices=STAGE_CHOICES, default=STAGE_OPEN)

    def __str__(self):
        return self.project_name

    @property
    def accepted_proposal(self):
        return self.comments.filter(state=Comment.ACCEPTED).first()


class Comment (models.Model):
    """A proposal (response) to a project from anyone who wants to work on it."""
    post = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(max_length=100, default= "")
    response = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    proposed_price = models.CharField(max_length=60, blank=True)
    timeline = models.CharField(max_length=60, blank=True, help_text='e.g. "2 weeks"')
    PENDING, ACCEPTED, DECLINED = 'pending', 'accepted', 'declined'
    STATE_CHOICES = ((PENDING, 'Pending'), (ACCEPTED, 'Accepted'), (DECLINED, 'Declined'))
    state = models.CharField(max_length=10, choices=STATE_CHOICES, default=PENDING)
    # private link for the proposer, who has no account
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def __str__(self):
        return self.name


class Milestone(models.Model):
    """Agreed deliverables for a project once a proposal is accepted (tracking only, no payments)."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=120)
    due_date = models.DateField(null=True, blank=True)
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', 'created_at']

    def __str__(self):
        return self.title
    

class TermsAndConditions(models.Model):
    terms_and_conditions = models.TextField()
    
    def __str__(self):
        return self.terms_and_conditions