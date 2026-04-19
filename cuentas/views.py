from django.shortcuts import render

def login(request):
    return render (request,"login.html")

def registro(request):
    return render (request,"registro.html")


def restablecer(request):
    return render (request,"restablecer.html")

