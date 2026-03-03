from django.shortcuts import render

def home(request):
    """
    Homepage view: renders the skeleton of the finance sheet generator
    """
    return render(request, "main/home.html") 