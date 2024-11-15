from django.contrib.auth import authenticate, login as auth_login, logout
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.signals import user_logged_out
from django.contrib.auth.models import User
from .forms import EnrollForm, MessageForm, TeacherForm
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from django.dispatch import receiver
from django.urls import reverse
from .models import Student, Message, Teacher, Subject
import logging
from django.views.decorators.csrf import csrf_exempt
import asyncio
from django.http.response import StreamingHttpResponse
from django.http import StreamingHttpResponse
from django.views import View

class MyAsyncView(View):
    async def get(self, request, *args, **kwargs):
        async def async_data_generator():
            for i in range(10):  # Simulating data generation
                yield f"Data chunk {i}\n"
                await asyncio.sleep(1)  # Simulate a delay

        # Use AsyncStreamingHttpResponse if you are on Django 4.1 or later
        response = StreamingHttpResponse(async_data_generator())
        response['Content-Type'] = 'text/plain'
        return response

async def iterable_content():
    for _ in range(5):
        await asyncio.sleep(1)
        print('Returning chunk')
        yield b'a' * 10000

def test_stream_view(request):
    return StreamingHttpResponse(iterable_content())

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)

#working properly
def logout_view(request):
    """Log the user out and redirect to the home page."""
    logout(request)
    return redirect('home')

def home(request):
    """Render home page."""
    student = Student.objects.all()  # Fetch all students
    return render(request, 'general/home.html', {'student':student})

def teacher_list(request):
    """Render home teacher list."""
    teachers = Teacher.objects.all()  # Fetch all students
    return render(request, 'superuser/teacher_list.html', {'teacher': teacher})

def community(request):
    """Render community page."""
    return render(request, 'school/community.html')

def event(request):
    """Render event page."""
    return render(request, 'school/event.html')

def courses(request):
    """Render courses page."""
    return render(request, 'school/courses.html')

def contact(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.student = request.user.student  # Assuming you have a user model linked to Student
            message.save()
            return redirect('contact')  # Redirect to the same page or another page
    else:
        form = MessageForm()

    messages = Message.objects.all()  # Fetch all messages
    return render(request, 'school/contact.html', {'form': form, 'messages': messages})

def approve_message(request, message_id):
    message = Message.objects.get(id=message_id)
    message.approved = True
    message.save()
    return redirect('contact')  # Redirect back to the message list

def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    message.delete()
    return redirect('contact')


def user_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        teacher = authenticate(request, email=email, password=password)
        
        if teacher is not None:
            login(request, teacher)
            return redirect('home')  # Redirect to a home page or dashboard
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')

    return render(request, 'login.html')

def success(request):
    """Render success page."""
    return render(request, 'general/success.html')

def access_denied(request):
    """Render access denied page."""
    return render(request, 'general/access_denied.html')

def privacy_policy(request):
    """Render privacy policy page."""
    return render(request, 'general/privacy_policy.html')

def terms_of_service(request):
    """Render terms of service page."""
    return render(request, 'general/terms_of_service.html')


#working properly (maintain) if you add, change or remove (models or form) you should change something here
def enroll(request):
    """Handle student enrollment."""
    if request.method == 'POST':
        form = EnrollForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            
            # Check if the username already exists
            if User.objects.filter(username=username).exists():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': {'username': ['Username already exists. Please choose a different one.']}})
                else:
                    messages.error(request, 'Username already exists. Please choose a different one.')
                    return render(request, 'information/enroll.html', {'form': form})

            # Create a new User instance
            user = User.objects.create_user(
                username=username,
                password=form.cleaned_data['password'],
                email=form.cleaned_data['email'],
            )

            # Set additional fields
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()  # Save the user instance
            
            # Create a new Student instance
            student = Student(
                user=user,
                username=user.username,
                email=user.email,
                first_name=form.cleaned_data['first_name'],
                middle_name=form.cleaned_data.get('middle_name', ''),
                last_name=form.cleaned_data['last_name'],
                address=form.cleaned_data['address'],
                phone=form.cleaned_data['phone'],
                sex=form.cleaned_data['sex'],
                mother_tongue=form.cleaned_data['mother_tongue'],
                religion=form.cleaned_data['religion'],
                learning_mode=form.cleaned_data['learning_mode'],
                payment_method=form.cleaned_data['payment_method'],
                strand=form.cleaned_data['strand'],
                branch=form.cleaned_data['branch'],
                emergency_contact_name=form.cleaned_data['emergency_contact_name'],
                emergency_contact_phone=form.cleaned_data['emergency_contact_phone'],
                emergency_contact_relationship=form.cleaned_data['emergency_contact_relationship'],
                emergency_contact_email=form.cleaned_data['emergency_contact_email'],
            )

            try:
                student.save()  # Save the student instance
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Enrollment successful!'})
                else:
                    messages.success(request, 'Student enrolled successfully!')
                    return redirect('success')  # Redirect to success page
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': {'general': [f'Error enrolling student: {e}']}})
                else:
                    messages.error(request, f'Error enrolling student: {e}')
                    return render(request, 'information/enroll.html', {'form': form})
        else:
            # Return errors as a JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
            else:
                return render(request, 'information/enroll.html', {'form': form})
    else:
        form = EnrollForm()

    return render(request, 'information/enroll.html', {'form': form})
    
#working properly? not sure yet I haven't check this
@login_required
def student_list(request):
    """Display list of students for admin users."""
    if not request.user.is_superuser:
        return redirect('access_denied')

    students = Student.objects.all()  # Fetch all students
    return render(request, 'teacher/student_list.html', {'students': students})

#working properly? not sure yet I haven't check this
@login_required
def user_list(request):
    """Display list of users for admin users."""
    if not request.user.is_superuser:
        return redirect('access_denied')

    users = User.objects.all()  # Fetch all users
    return render(request, 'superuser/user_list.html', {'users': users})

#working properly? not sure yet I haven't check this
@login_required
def edit_student(request, student_id):
    """Edit student information."""
    student = get_object_or_404(Student, student_id=student_id)

    if request.method == 'POST':
        form = EnrollForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student information updated successfully!')
            return redirect('student_list')
        else:
            messages.error(request , 'Please correct the errors below.')
    else:
        form = EnrollForm(instance=student)
  
    return render(request, 'edit-delete/edit_student.html', {'form': form, 'student': student})

#working properly? not sure yet I haven't check this
@login_required
def delete_student(request, student_id):
    """Delete a student."""
    student = get_object_or_404(Student, student_id=student_id)
    student.delete()
    messages.success(request, 'Student deleted successfully!')
    return redirect('student_list')  # Redirect to the student list page

#working properly
def login(request):
    """Handle user login."""
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        # Use the email to authenticate
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            auth_login(request, user)
            return redirect(request.GET.get('next', 'home'))
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, 'user-interface/login.html')

@login_required
def profile(request):
    student = None
    teacher = None
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            pass
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            pass
    return render(request, 'user-interface/profile.html', {'student':student, 'teacher': teacher})

def approve_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    # Implement your approval logic here. For example:
    student.is_approved = True  # Assuming you have an 'is_approved' field
    student.save()
    return redirect('your_student_list_view')  # Redirect to the student list view

#still process
def stem_view(request):
    # Logic for the STEM strand (e.g., fetch related data)
    return render(request, 'strands/stem.html')

def abm_view(request):
    # Logic for the ABM strand
    return render(request, 'strands/abm.html')

def humss_view(request):
    # Logic for the HUMSS strand
    return render(request, 'strands/humss.html')

def gas_view(request):
    # Logic for the GAS strand
    return render(request, 'strands/gas.html')

def tvl_view(request):
    # Logic for the TVL strand
    return render(request, 'strands/tvl.html')

def la_forteza(request):
    # Logic for the TVL strand
    return render(request, 'branch/la_forteza.html')

def login_branch(request):
    return render(request, 'branch/login_branch.html')

def dashboard(request):
    students = Student.objects.all()  # Fetch all students
    return render(request, 'teacher/dashboard.html', {'students': students})

def grading(request, student_id):
    students = Student.objects.all()  # Fetch all students
    return render(request, 'teacher/grading.html')

def subject(request):
    return render(request, 'teacher/subject.html')

def lesson(request):
    return render(request, 'teacher/lesson.html')

def add_login_teacher(request):
    return render(request, 'teacher/teacher.html')

def teacher_register(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('teacher_list')
        else:
            print(form.errors) 
    else:
        form = TeacherForm()
    return render(request, 'superuser/teacher.html', {'form': form})

def update_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    if request.method == 'POST':
        form = TeacherForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            return redirect('teacher_list')
    else:
        form = TeacherForm(instance=teacher)
    return render(request, 'teacher_list.html', {'form': form})

def add_subject(request):
    if request.method == 'POST':
        subject_name = request.POST.get('name')
        teacher_id = request.POST.get('teacher_id')  # Get the teacher ID from the request
        try:
            teacher = Teacher.objects.get(id=teacher_id)  # Assuming you have a Teacher model
            subject = Subject(name=subject_name)
            subject.save()
            teacher.subjects.add(subject)  # Associate the subject with the teacher
            return JsonResponse({'success': True})
        except Teacher.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Teacher not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@csrf_exempt
def edit_subject(request):
    if request.method == 'POST':
        subject_id = request.POST.get('id')
        subject_name = request.POST.get('name')
        if not subject_id or not subject_name:
            return JsonResponse({'success': False, 'error': 'Missing subject ID or name'}, status=400)
        try:
            subject = Subject.objects.get(id=subject_id)
            subject.name = subject_name
            subject.save()
            return JsonResponse({'success': True})
        except Subject.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Subject not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@csrf_exempt
def remove_subject(request):
    if request.method == 'POST':
        subject_id = request.POST.get('id')
        if not subject_id:
            return JsonResponse({'success': False, 'error': 'Missing subject ID'}, status=400)
        try:
            subject = Subject.objects.get(id=subject_id)
            subject.delete()
            return JsonResponse({'success': True})
        except Subject.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Subject not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
