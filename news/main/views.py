from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Profile, User, News, Category, Tag, WatchLater, View
from django.contrib import messages
from django import forms
from django.db.models import Q
from django.utils import timezone

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('profile')
    else:
        form = RegisterForm()
    return render(request, 'main/register.html', {'form': form})

@login_required
def profile(request):
    profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        profile.first_name = request.POST.get('first_name', profile.first_name)
        profile.last_name = request.POST.get('last_name', profile.last_name)
        profile.contact_info = request.POST.get('contact_info', profile.contact_info)
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        profile.save()
        messages.success(request, 'Профиль обновлен!')
    return render(request, 'main/profile.html', {'profile': profile})

# --- Новости ---

def news_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    tag_id = request.GET.get('tag')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    news = News.objects.filter(is_published=True)
    if query:
        news = news.filter(Q(title__icontains=query) | Q(text__icontains=query))
    if category_id:
        news = news.filter(category_id=category_id)
    if tag_id:
        news = news.filter(tags__id=tag_id)
    if date_from:
        news = news.filter(pub_date__gte=date_from)
    if date_to:
        news = news.filter(pub_date__lte=date_to)
    news = news.order_by('-pub_date').distinct()
    categories = Category.objects.all()
    tags = Tag.objects.all()
    return render(request, 'main/news_list.html', {
        'news_list': news,
        'categories': categories,
        'tags': tags,
        'query': query,
        'category_id': category_id,
        'tag_id': tag_id,
        'date_from': date_from,
        'date_to': date_to,
    })

def news_detail(request, pk):
    news = News.objects.get(pk=pk)
    if news.is_published or (request.user.is_authenticated and (request.user == news.author or request.user.role == 'admin')):
        # Учет просмотра
        if request.user.is_authenticated:
            View.objects.get_or_create(user=request.user, news=news)
        news.views_count = View.objects.filter(news=news).count()
        news.save()
        is_watch_later = False
        if request.user.is_authenticated:
            is_watch_later = WatchLater.objects.filter(user=request.user, news=news).exists()
        return render(request, 'main/news_detail.html', {'news': news, 'is_watch_later': is_watch_later})
    else:
        messages.error(request, 'Новость не опубликована')
        return redirect('news_list')

@login_required
def news_create(request):
    class NewsForm(forms.ModelForm):
        class Meta:
            model = News
            fields = ['title', 'text', 'image', 'category', 'tags', 'is_published']
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user
            news.save()
            form.save_m2m()
            messages.success(request, 'Новость создана!')
            return redirect('news_detail', pk=news.pk)
    else:
        form = NewsForm()
    return render(request, 'main/news_form.html', {'form': form})

@login_required
def news_edit(request, pk):
    news = News.objects.get(pk=pk)
    if request.user != news.author and request.user.role != 'admin':
        messages.error(request, 'Нет доступа')
        return redirect('news_detail', pk=pk)
    class NewsForm(forms.ModelForm):
        class Meta:
            model = News
            fields = ['title', 'text', 'image', 'category', 'tags', 'is_published']
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            form.save()
            messages.success(request, 'Новость обновлена!')
            return redirect('news_detail', pk=news.pk)
    else:
        form = NewsForm(instance=news)
    return render(request, 'main/news_form.html', {'form': form, 'edit': True})

@login_required
def news_delete(request, pk):
    news = News.objects.get(pk=pk)
    if request.user != news.author and request.user.role != 'admin':
        messages.error(request, 'Нет доступа')
        return redirect('news_detail', pk=pk)
    if request.method == 'POST':
        news.delete()
        messages.success(request, 'Новость удалена!')
        return redirect('news_list')
    return render(request, 'main/news_confirm_delete.html', {'news': news})

@login_required
def add_watch_later(request, pk):
    news = News.objects.get(pk=pk)
    WatchLater.objects.get_or_create(user=request.user, news=news)
    messages.success(request, 'Добавлено в "Посмотреть позже"!')
    return redirect('news_detail', pk=pk)

@login_required
def remove_watch_later(request, pk):
    news = News.objects.get(pk=pk)
    WatchLater.objects.filter(user=request.user, news=news).delete()
    messages.success(request, 'Удалено из "Посмотреть позже"!')
    return redirect('news_detail', pk=pk)

@login_required
def watch_later_list(request):
    news = News.objects.filter(watchlater__user=request.user)
    return render(request, 'main/watch_later_list.html', {'news_list': news})

from django.contrib.auth import logout as auth_logout

def logout_view(request):
    auth_logout(request)
    return render(request, 'main/logout.html')
