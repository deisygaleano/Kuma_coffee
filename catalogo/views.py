from django.shortcuts import render

def lista(request):
    return render(request,'catalogo.html')
    

def detalle_producto(request):
    return render(request,'detalle_producto.html')


