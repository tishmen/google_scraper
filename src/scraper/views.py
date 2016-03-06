from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from .models import GooglePage


def html_view(request, pk):
    '''display stored html from search as a page'''
    html_response = get_object_or_404(GooglePage, pk=pk)
    return HttpResponse(html_response.html)
