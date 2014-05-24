from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

from tourneys.models import *

def match(request):
    try:
        match = Match.objects.filter(finished=False).order_by('?')[:1].get()
    except Match.DoesNotExist:
        match = None
    context = { 'match': match }
    return render(request, 'tourneys/match.html', context)

def matchsubmit(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    try:
        winners = match.competitor_set\
            .filter(pk__in=request.POST.getlist('competitors'))
    except Competitor.DoesNotExist:
        return HttpResponse('Competitor does not exist.')
    for competitor in winners:
        competitor.winner = True
        competitor.save()
    match.finished = True
    match.save()
    return HttpResponseRedirect(reverse('tourneys:match'))

