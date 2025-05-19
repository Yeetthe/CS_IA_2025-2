from django.shortcuts import render, redirect, get_object_or_404
from .models import Event, UserModel
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import EventForm, SignUpForm, AdminCloneEventForm
import calendar
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages


def home(request):
    return render(request, 'base.html')

#@login_required
#def save_shared_event(request):
#    if request.methood == "POST":
#        form = EventForm(request.POST, request.FILES)
#        if form.is_valid():
#            event = form.save(commit=False)
#            event.user = request.user
#            form.save()
#            return redirect("calendar_view")
#        else:
#            form = EventForm()
#        return render(request, "events/shared_event.html", {'form': form})

@login_required
def dashboard_view(request):
    today = datetime.today().date()
    upcoming_events = Event.objects.filter(user=request.user, date__gte=today).order_by('date')[:5]
    return render(request, 'dashboard.html', {'events': upcoming_events})

@login_required
def assign_child_view(request):
    if request.user.role != 'parent':
        return HttpResponseForbidden("Only parents can assign children.")

    form = AssignChildForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        child = form.cleaned_data['child_username']
        request.user.children.add(child)
        messages.success(request, f"Assigned {child.username} as your child.")
        return redirect('dashboard')  # or your chosen view

    return render(request, 'events/assign_child.html', {'form': form})


def shared_event_view(request, token):
    event = get_object_or_404(Event, share_token=token)

    if request.method == 'POST':
        if request.user.is_authenticated:
            Event.objects.create(
                user=request.user,
                title=event.title,
                description=event.description,
                date=event.date
            )
            return redirect('calendar')
        else:
            return redirect('login')

    return render(request, 'events/shared_event.html', {'event': event})


@login_required
def event_list(request):
    events = Event.objects.filter(user=request.user)
    return render(request, "events/event_list.html", {"events": events})

@login_required
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            form.save()
            return redirect("calendar")
    else:
        form = EventForm()
    return render(request, "events/create_event.html", {"form": form})

#def calender(request):
#    events = Event.objects.all()
#    return render(request, "events/calendar.html", {"events": events})


@login_required
def calendar_view(request):
    today = datetime.today()
    current_year = today.year
    current_month = today.month

    user = request.user

    # Determine which events to show based on role:
    if user.role == 'admin':
        # Admin: view all or a specific student
        student_username = request.GET.get('student')
        if student_username:
            target = get_object_or_404(UserModel, username=student_username, role='student')
            events_qs = Event.objects.filter(user=target)
            viewing = target.username
        else:
            events_qs = Event.objects.all()
            viewing = 'All Users'
    elif user.role == 'parent':
        # Parent: view all children or a chosen one
        child_username = request.GET.get('child')
        children = user.children.all()  # M2M field on parent
        if child_username:
            target = get_object_or_404(UserModel, username=child_username, role='student', parents=user)
            events_qs = Event.objects.filter(user=target)
            viewing = target.username
        else:
            events_qs = Event.objects.filter(user__in=children)
            viewing = 'All My Children'
    else:
        # Student (and default): only own events
        events_qs = Event.objects.filter(user=user)
        viewing = user.username

    # Build a date→events map
    events_by_date = {}
    for ev in events_qs:
        events_by_date.setdefault(ev.date, []).append(ev)

    # Generate calendar grid
    month_calendar = calendar.Calendar().monthdatescalendar(current_year, current_month)
    calendar_data = []
    for week in month_calendar:
        week_data = []
        for day in week:
            week_data.append({
                'date': day,
                'events': events_by_date.get(day, [])
            })
        calendar_data.append(week_data)

    return render(request, 'events/calendar.html', {
        'calendar_weeks': calendar_data,
        'current_month': current_month,
        'current_year': current_year,
        'role': user.role,
        'viewing': viewing,
    })


@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, user=request.user)

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('event_list')
    else:
        form = EventForm(instance=event)

    return render(request, 'events/edit_event.html', {'form': form})

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, user=request.user)

    if request.method == 'POST':
        event.delete()
        return redirect('event_list')

    return render(request, 'events/confirm_delete.html', {'event': event})


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
@user_passes_test(is_admin)
def admin_clone_event(request, event_id):
    """
    Allows an admin to clone an existing event to a specified student's calendar.
    """
    original = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = AdminCloneEventForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['student_username']
            try:
                student = UserModel.objects.get(username=username, role='student')
            except User.DoesNotExist:
                messages.error(request, f"No student found with username '{username}'.")
                return redirect('admin_clone_event', event_id=event_id)

            # Clone the event
            Event.objects.create(
                user=student,
                title=original.title,
                description=original.description,
                date=original.date,
                file=original.file
            )
            messages.success(request, f"Event cloned to {student.username}.")
            return redirect('event_list')
    else:
        form = AdminCloneEventForm()

    return render(request, 'events/admin_clone_event.html', {
        'form': form,
        'original_event': original
    })


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'account/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('calendar')
        else:
            return redirect('login')

    return render(request, 'account/login.html')


#def register_view(request):
#    if request.method == "POST":
#        username = request.POST["username"]
#        password = request.POST["password"]
#
#        if UserModel.objects.filter(username=username).exists():
#            return render(request, "account/signup.html", {"error": "Username taken"})
#
#        user = UserModel(username=username)
#        user.set_password(password)  # Hash password before saving
#        user.save()
#
#        return redirect("login")  # Redirect to login page
#
#    return render(request, "account/signup.html")

def logout_view(request):
    # call django’s built in logout() to clear auth related session keys:
    # '_auth_user_id'
    # '_auth_user_backend'
    # '_auth_user_hash'
    logout(request)

    # clear the session to remove any remaining data:
    # ensures no residual cookies or session data persist.
    request.session.flush()

    # redirect the user to the login page to complete the logout cycle.
    return redirect("login")

