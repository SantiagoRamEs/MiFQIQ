from django.urls import path, include
from . import views

from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


#API
router = routers.DefaultRouter()
router.register(r"Professor", views.ProfessorViewSet)
router.register(r"User", views.UserViewSet)
router.register(r"ProfessorCourse", views.ProfessorCourseViewSet)
router.register(r"Course", views.CourseViewSet)
router.register(r"Grade", views.GradeViewSet)



urlpatterns =[
    path('', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),

    path('professors/', views.view_professors, name = 'professors'),
    path("completar-perfil/", views.completar_perfil, name="completar_perfil"),
    path('professors/<int:pk>/', views.profile_professor, name = 'profile_professor'),
    path('suggest_professor/', views.suggest_professor, name = 'suggest_professor'),

    path('grade/create/<int:pc_id>/',views.create_grade,name='creategrade'),
    path('grade/edit/<int:grade_id>/',views.edit_grade,name='editgrade'),
    
    path('mis-calificaciones/', views.my_grades, name = 'my_grades'),
    path('my-grades/delete/<int:grade_id>/', views.delete_grade, name='delete_grade'),


    #API
    path('api/', include(router.urls)),

    
    #DOCUMENTATION
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

]
