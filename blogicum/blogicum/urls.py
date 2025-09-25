from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from django.urls import include, path, reverse


class UserRegisterView(CreateView):
    template_name = 'registration/registration_form.html'
    form_class = UserCreationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.object.username}
        )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('pages/', include('pages.urls')),
    path('', include('blog.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path(
        'auth/registration/',
        UserRegisterView.as_view(),
        name='registration',
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler403 = 'blog.views.csrf_failure'
handler404 = 'blog.views.page_not_found'
handler500 = 'blog.views.error_500'
