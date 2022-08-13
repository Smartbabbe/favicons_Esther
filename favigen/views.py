from datetime import datetime
from django.shortcuts import render
from django.http import FileResponse
from django.core.files import File
from django.core.files.storage import FileSystemStorage

from django.shortcuts import render, redirect
from favigen.forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from pathlib import Path
from .models import *
from .utils import zippify
from .utils import utility
from .utils.favigenerator import generate_favicon


import os
import re

# Create your views here.
def home_page(request):
    return render(request, "favigen/home.html")


def signup_page(request):
    """
    This view renders the signup page and then takes in user data 
    (First Name, Email and Password) from the HTML form as a POST request.
    It then extracts the user's first name from the form and uses it in a 
    custom message if the registration is successful, after which it 
    redirects the user to the home page.
    """
    # if not request.user.is_anonymous:
    #     return redirect("favigen:home")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            f_name = form.cleaned_data.get("first_name")
            messages.success(request, f"Registration successful for {f_name}")
            return redirect("favigen:home")
        messages.error(request, "Unsuccessful registration. Invalid information.")

    form = CustomUserCreationForm()
    return render(
        request=request,
        template_name="favigen/sign-up.html",
        context={"signup_form": form},
    )


def login_page(request):
    user = request.user
    # if user.is_authenticated:
    #     return redirect("favigen:home")

    if request.POST:
        form = CustomAuthenticationForm(request.POST)
        email = request.POST.get("email")
        password = request.POST.get("password")

        if user := authenticate(email=email, password=password):
            login(request, user)
            messages.success(request, "Logged In")
            return redirect("favigen:home")
        else:
            messages.error(request, "Please enter correct details")
    else:
        form = CustomAuthenticationForm()

    context = {"login_form": form}
    return render(request, "favigen/login.html", context)


def logout_view(request):
    logout(request)
    messages.success(request, "Logged Out")
    return redirect("favigen:login")


# @login_required
@login_required(login_url='fav:login')
def image_upload(request):
    user = request.user
    context = {}

    if request.method == "POST":
        image_file = request.FILES["document"]
        title = request.POST.get("title")
        favourite = bool(request.POST.get("favourite"))

        fs = FileSystemStorage()
        name = fs.save(name=image_file.name, content=image_file)
        url_img = fs.url(name)

        file_path = f"static/media/{image_file.name}"
        favs_dir = "static/media/favs/"
        f_type = image_file.name.split(".")[-1]
        f_size = os.path.getsize(file_path)

        # To generate a new file name, we get the current date and time 
        # and add a prefix to it then join the extension at the end
        a = f"FAV{str(datetime.now())}"
        b = ''.join(re.split(r'-|\.|:|\ ', a))
        new_name = f"{b}.{f_type}"

        # Generate favicons and zip them
        embed_link = generate_favicon(file_path, favs_dir)

        img = Image.objects.create(
            title=title,
            uploaded_image=image_file,
            favourite=favourite,
            uploaded_by=user)
        img.save()

        user_dir = f"static/media/user_{user.id}"
        zippify.zippify(favs_dir, user_dir, b)


        fav = Favicon.objects.create(
            image=img,
            original_filename=name, 
            new_filename=new_name,
            file_type=f_type,
            file_byte_size=f_size,
            embed_link=embed_link)
        fav.save()

        saved_fav = Favicon.objects.get(new_filename=new_name)
        path = Path(os.path.join(user_dir, f"{b}.zip"))
        with path.open(mode='rb') as f:
            saved_fav.zipped_favs = File(f, name=path.name)
            saved_fav.save()

        # Rename the saved favicon
        former_name = os.path.join(user_dir, image_file.name)
        new_name = os.path.join(user_dir, new_name)
        os.rename(former_name, new_name)

        utility.delete(favs_dir)

        # f_zip = open(os.path.join(user_dir, f"{b}.zip"), 'rb')

        context["url_img"] = url_img
        # context["url_zip"] = 
    return render(request, "favigen/upload.html", context)


def contact_page(request):
    return render(request, "favigen/contact.html")


@login_required(login_url='fav:login')
def saved_icons(request):
    return render(request, "favigen/saved-icons.html")


@login_required(login_url='fav:login')
def generated_icon(request):
    return render(request, "favigen/generated-icon.html")


@login_required(login_url='fav:login')
def generate_icon(request):
    return render(request, "favigen/index.html")