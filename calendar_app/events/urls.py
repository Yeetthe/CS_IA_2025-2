from django.conf.urls.static import static
from django.urls import path
from .views import home, shared_event_view, event_list, delete_event, edit_event, create_event, calendar_view, dashboard_view, signup_view, login_view, logout, admin_clone_event, assign_child_view
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('list/', event_list, name='event_list'),  # Shows the list of events
    path('create/', create_event, name='create_event'),  # Event creation page
    path('calendar/', calendar_view, name='calendar'), # Calendar page
    path('edit/<int:event_id>/', edit_event, name='edit_event'), #Edit Events page
    path('event/delete/<int:event_id>/', delete_event, name='delete_event'), # Delete Events path
    path('share/<uuid:token>/', shared_event_view, name='shared_event'), # Share Events page
    path('clone/<int:event_id>/', admin_clone_event, name='admin_clone_event'),
    path('login/', login_view, name='login'), # Login Page
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', signup_view, name='signup'), # Signup Page
    path('assign-child/', assign_child_view, name='assign_child'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



