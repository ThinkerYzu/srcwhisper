from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login


from django.forms import EmailField
from django.contrib.auth.models import User


class UserCreationForm(UserCreationForm):
    email = EmailField(label="Email address", required=True,
                       help_text="Required.")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

        def save(self, commit=True):
            user = super(UserCreationForm, self).save(commit=False)
            user.email = self.cleaned_data["email"]
            if commit:
                user.save()
                pass
            return user
        pass
    pass

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
