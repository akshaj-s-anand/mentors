from django.shortcuts import render, get_object_or_404, redirect
from .models import Mentors, Specialization, Category, Mentee
from .forms import MenteeForm
from django.contrib import messages


def index(request):
    mentors = Mentors.objects.all()
    specializations = Specialization.objects.all()
    categorys = Category.objects.all()
    title = 'Home'
    username = None
    sitename = 'futurfounder.com'
    if request.user.is_authenticated:
        username = request.user.username
    context = {
        'mentors': mentors,
        'specializations': specializations,
        'categorys': categorys,
        'title': title,
        'username': username,
        'sitename': sitename,
    }
    return render(request, 'mentorapp/index.html', context)

# def footer(request):
    mentors = Mentors.objects.all()
    specializations = Specialization.objects.all()
    categorys = Category.objects.all()
    context = {
        'mentors': mentors,
        'specializations': specializations,
        'categorys': categorys,
    }
    return render(request, 'mentorapp/footer.html', context)


def category_page(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    mentors_in_category = category.mentors.all()
    categorys = Category.objects.all()
    title = category
    specializations = Specialization.objects.filter(mentors__in=mentors_in_category).distinct()
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    context = {
        'category': category,
        'mentors': mentors_in_category, 
        'categorys':categorys, 
        'title':title, 
        'specializations':specializations,
        'username' : username
    }
    
    return render(request, 'mentorapp/category_page.html', context)

def all_mentors(request):
    title = 'Find your Mentor'
    categorys = Category.objects.all()
    mentors = Mentors.objects.all()
    specializations = Specialization.objects.all()
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    context = {
        'title' : title,
        'categorys':categorys,
        'mentors': mentors,
        'specializations': specializations,
        'username' : username
    }
    return render(request, 'mentorapp/all_mentors.html', context)



def mentor_details_view(request, mentor_id):
    mentor = get_object_or_404(Mentors, pk=mentor_id)
    categorys = Category.objects.all()
    title = mentor
    username = request.user.username if request.user.is_authenticated else None

    if request.method == 'POST':
        form = MenteeForm(request.POST)
        if form.is_valid():
            mentor_name = form.cleaned_data['mentor_name']
            mentee_name = form.cleaned_data['mentee_name']
            contact_number = form.cleaned_data['contact_number']
            mentee_requirement = form.cleaned_data['mentee_requirement']
            # Extracting mentor contact from the hidden field
            mentor_contact = request.POST.get('mentor_contact')

            # Save Mentee information
            mentee = Mentee(
                mentor_name=mentor_name,
                mentee_name=mentee_name,
                contact_number=contact_number,
                mentee_requirement=mentee_requirement,
                mentor_contact=mentor_contact,
            )
            mentee.save()

            messages.success(request, 'Your request is in review')
            return redirect('mentor_details', mentor_id=mentor.id)
        else:
            messages.error(request, 'Form validation failed. Please check the entered data.')
    else:
        form = MenteeForm()

    context = {
        'categorys': categorys,
        'mentor': mentor,
        'title': title,
        'username': username,
        'form': form
    }

    return render(request, 'mentorapp/mentor_details.html', context)

