"""
Creates and save a translation matrix between leagues based on the results of
tournaments.
"""

from optparse import make_option

from django.core.management.base import CommandError

from TourneysCommand import TourneysCommand
from tourneys.models import *

import pickle
import numpy as np
from sklearn.preprocessing import normalize

class Command(TourneysCommand):
    args = '[options] <targetleague sourceleague>'
    help = ('Creates and save a translation matrix between leagues based on '
            'the results of tournaments.')
    option_list = TourneysCommand.option_list + (
        make_option('--debug', dest='debug', action='store_true', 
            default=False, help='Output debugging information'
        ),
        make_option('--savefile', dest='savefile', 
            default='tourney_topic_map.pickle',
            help='Name of pickle to write topic map to.', metavar='FILE'
        ),
    )

    def getTournaments(self, targetleague, sourceleague):
        for targetteam in Team.objects.filter(attribute__league=targetleague):
            try:
                tournament = Tournament.objects\
                                       .filter(league=sourceleague)\
                                       .filter(targetteam=targetteam).get()
            except Tournament.DoesNotExist:
                raise CommandError(
                    ('Tournament not found for sourceleague=%s and '
                     'targetteam=%s') % (sourceleague, targetteam)
                )
            yield tournament
    
    def buildDictionaryFromLeague(self, league):
        teamIdxs = {}
        idx = 0
        for team in Team.objects.filter(attribute__league=league):
            teamIdxs[team] = idx
            idx += 1
        return teamIdxs

    def buildAttributeDictionary(self, teamIdxs):
        attIdxs = {}
        idx = 0
        for team in sorted(teamIdxs):
            if team.attribute not in attIdxs:
                attIdxs[team.attribute] = idx
                idx += 1
        return attIdxs

    def getAttributeMatrix(self, matrix, sourceTeamIdxs, targetTeamIdxs):
        sourceAttIdxs = self.buildAttributeDictionary(sourceTeamIdxs)
        targetAttIdxs = self.buildAttributeDictionary(targetTeamIdxs)
        attMatrix = np.zeros([len(sourceAttIdxs), len(targetAttIdxs)])
        for sourceTeam in sourceTeamIdxs:
            for targetTeam in targetTeamIdxs:
                value = matrix[sourceTeamIdxs[sourceTeam],
                        targetTeamIdxs[targetTeam]]
                sign = (1 if sourceTeam.positive == targetTeam.positive else -1)
                attRow = sourceAttIdxs[sourceTeam.attribute]
                attCol = targetAttIdxs[targetTeam.attribute]
                attMatrix[attRow, attCol] += value*sign
        return normalize(attMatrix, 'l1', axis=0), sourceAttIdxs, targetAttIdxs
        
    #TODO: Clean up - remove debug option
    def handle(self, *args, **options):
        # parse command line
        if len(args) != 2:
            raise CommandError('Must provide targetleague and sourceleage')
        targetleague_name = args[0]
        sourceleague_name = args[1]
        debug = options['debug']
        savefile = options['savefile']

        # get targetleague
        try:
            targetleague = League.objects.get(name=targetleague_name)
        except League.DoesNotExist:
            raise CommandError('Cannot find targetleague: %s' %\
                               targetleague_name)
        # get sourceleague
        try:
            sourceleague = League.objects.get(name=sourceleague_name)
        except League.DoesNotExist:
            raise CommandError('Cannot find sourceleague: %s' %\
                               sourceleague_name)

        # create matrix indexes for teams of each league
        sourceTeamIdxs = self.buildDictionaryFromLeague(sourceleague)
        targetTeamIdxs = self.buildDictionaryFromLeague(targetleague)
        numSourceTeams = len(sourceTeamIdxs)
        numTargetTeams = len(targetTeamIdxs)

        teamMapper = np.zeros([numSourceTeams, numTargetTeams])
        col = 0

        # Get the tournaments
        for tournament in self.getTournaments(targetleague, sourceleague):
            if debug:
                self.stdout.write(
                    'DBG: Processing tournamet: %s' % tournament.name
                )
            ratios = np.zeros([numSourceTeams, numSourceTeams])
            row = 0
            # Get the competitions for this tournament
            for competition in tournament.competition_set.all():
                if debug:
                    self.stdout.write(
                        'DBG:     ==== Round %d Competition ====' %\
                        competition.round
                    )
                # Get the competitionteams for this competition
                firstTeamSelected = False
                for competitionteam in competition.competitionteam_set.all():
                    if competitionteam.score == 0.0:
                        ratios[row][sourceTeamIdxs[competitionteam.team]] = 1.0
                        row += 1
                    elif not firstTeamSelected:
                        firstTeam = competitionteam
                        firstTeamSelected = True
                    else:
                        ratios[row][sourceTeamIdxs[firstTeam.team]] =\
                                competitionteam.score/firstTeam.score
                        ratios[row][sourceTeamIdxs[competitionteam.team]] =\
                                -1.0
                        row += 1
                    if debug:
                        self.stdout.write(
                            'DBG:     team %d (%s), score=%0.3f' % (
                                sourceTeamIdxs[competitionteam.team],
                                competitionteam.team,
                                competitionteam.score
                            )
                        )
            # Add row so that weights sum to 1
            ratios[row] = np.ones(numSourceTeams)
            if debug:
                self.stdout.write( 'RATIOS:')
                np.savetxt(self.stdout, ratios, '%.2f')

            # Solve system of equations
            y = np.zeros(numSourceTeams)
            y[numSourceTeams-1] = 1.0
            solution = np.dot(np.linalg.inv(ratios), y)
            if debug:
                self.stdout.write( 'SOLUTION:')
                np.savetxt(self.stdout, solution, '%.2f')

            # Add to teamMapper matrix
            teamMapper[:, col] = solution
            col += 1

        if debug:
            self.stdout.write( 'TEAM MAPPING:')
            np.savetxt(self.stdout, teamMapper, '%.3f')
            self.stdout.write()

        # create topic teamMapper matrix
        results = self.getAttributeMatrix(teamMapper, sourceTeamIdxs, targetTeamIdxs)
        topicMapper = results[0]
        np.savetxt(self.stdout, topicMapper)
        pickle.dump(topicMapper, open(savefile, 'w'))
