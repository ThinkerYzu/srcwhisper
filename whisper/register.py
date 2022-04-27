from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/whisper/code")
        pass

    form = UserCreationForm
    return render(request=request,
                  template_name = "whisper/register.html",
                  context={"form": form})
