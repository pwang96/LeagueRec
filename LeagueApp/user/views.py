from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.forms import Form

from user import models


# class ResultsView(generic.DetailView):
#     object = models.User
#     template_name = 'user/results.html'
#     context_object_name = 'user'

def results(request, username):
    user = get_object_or_404(models.User, name=username)
    return render(request, 'user/results.html', {'user': user,
                                                 'recommended_champs': user.get_recommended_champs(),
                                                 'top5_champs': user.get_top_5_played()})


def home(request):
    return render(request, 'home/home.html')


def handle_user(request):
    form = Form(request.POST)
    verboseName = request.POST['username']
    name = verboseName.replace(" ", "")
    if verboseName == '':
        return render(request, 'home/home.html', {
            'error_message': "Type in your summoner name!"
        })

    if not models.User.objects.filter(name=name).exists():
        curr_user = models.User(name=name, verbose_name=verboseName.capitalize())
        curr_user.process()
        curr_user.save()

    return HttpResponseRedirect(reverse('user:results', args=(name,)))