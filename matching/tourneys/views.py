from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello, world. You're at the poll index.")

def detail(request, tournament_id):
    return HttpResponse("You're looking at tourney %s." % tournament_id)

def results(request, tournament_id):
    return HttpResponse("You're looking at the results of tourney %s." %\
                        tournament_id)


