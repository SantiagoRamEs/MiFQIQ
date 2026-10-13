from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


#API
router = routers.DefaultRouter()
router.register(r"Professor", views.ProfessorViewSet)
router.register(r"User", views.UserViewSet)
router.register(r"ProfessorCourse", views.ProfessorCourseViewSet)
router.register(r"Course", views.CourseViewSet)
router.register(r"Grade", views.GradeViewSet)



urlpatterns =[
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('crear-cuenta/', views.register_view, name='register'),
    path(
        'recuperar-contrasena/',
        auth_views.PasswordResetView.as_view(
            template_name='password_reset_form.html',
            email_template_name='password_reset_email.html',
            subject_template_name='password_reset_subject.txt',
        ),
        name='password_reset',
    ),
    path(
        'recuperar-contrasena/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'restablecer-contrasena/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html',
        ),
        name='password_reset_confirm',
    ),
    path(
        'restablecer-contrasena/completo/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
    path('logout/', views.custom_logout, name='logout'),

    path('professors/', views.view_professors, name = 'professors'),
    path('professors/<int:pk>/', views.profile_professor, name = 'profile_professor'),
    path('suggest_professor/', views.suggest_professor, name = 'suggest_professor'),

    path('grade/create/<int:pc_id>/',views.create_grade,name='creategrade'),
    path('grade/edit/<int:grade_id>/',views.edit_grade,name='editgrade'),
    
    path('mis-calificaciones/', views.my_grades, name = 'my_grades'),
    path('my-grades/delete/<int:grade_id>/', views.delete_grade, name='delete_grade'),


    #API
    path('api/', include(router.urls)),
    #token
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    
    #DOCUMENTATION
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

]
