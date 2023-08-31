from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from iitr_drive import models

# Create your views here.
def home(request):
    context = {
        'folders': models.Folder.objects.all()
    }
    return render(request, 'iitr_drive/folders.html', context)

def register(request):
    if request.method == 'POST': 
        # form is instantiated and populated with data from request.POST   
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Your account has been created! You are now able to log in')
            return redirect('login')
    else:
        form = UserCreationForm()
        
    return render(request, 'home/register.html', {'form': form})
