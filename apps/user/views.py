from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest, Http404
from django.shortcuts import render, redirect, get_object_or_404

from .forms import UserForm, UserUpdateForm
from .utils.helpers import post_only
from .models import User


@login_required(login_url="/login/")
def user_profile(request, username=None):
    """ Handles user profile page. """
    username = username or request.user.username
    user = get_object_or_404(User, username=username)

    return render(request, "profile.html", {"profile": user})


@login_required(login_url="/login/")
def edit_profile(request):
    """ Handles user profile editing. """
    user = request.user

    if request.method == "GET":
        user_form = UserUpdateForm(instance=user)

    elif request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=user)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, "Profile settings saved")
            return redirect("apps.user:user_profile")
    else:
        raise Http404

    return render(request, "edit_profile.html", {"form": user_form})


def user_login(request):
    """
    Handles user authentication using Django's built-in authentication system.
    """

    if request.user.is_authenticated:
        return redirect("frontpage")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if not username or not password:
            return HttpResponseBadRequest()

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                redirect_url = request.POST.get("next") or "frontpage"
                return redirect(redirect_url)
            else:
                return render(request, "login.html", {"login_error": "Account disabled"})
        else:
            return render(request, "login.html", {"login_error": "Wrong username or password."})

    return render(request, "login.html")


@post_only
def user_logout(request):
    """
    Log out user if one is logged in and redirect them to frontpage.
    """

    if request.user.is_authenticated:
        redirect_page = request.POST.get("current_page", "/")
        logout(request)
        messages.success(request, "Logged out!")
        print(f"\n\nuser.is_authenticated: {request.user.is_authenticated}\n\n")
        return redirect(redirect_page)
    return redirect("frontpage")


def register(request):
    """
    Handles user registration using UserForm from forms.py
    Creates new User instance if appropriate data
    has been supplied.

    If account has been created user is redirected to login page.
    """
    user_form = UserForm()
    if request.user.is_authenticated:
        messages.warning(request, "You are already registered and logged in.")
        return redirect("frontpage")

    if request.method == "POST":
        user_form = UserForm(request.POST)
        if user_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            # user = authenticate(username=request.POST["username"], password=request.POST["password"])
            # login(request, user)
            return redirect("login")

    return render(request, "register.html", {"form": user_form})
