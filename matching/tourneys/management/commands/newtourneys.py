"""
Setup new tournaments or add a round to existing ones between two leagues.
"""

from optparse import make_option
import math
import random

from django.core.management.base import CommandError

from TourneysCommand import TourneysCommand
from tourneys.models import *

class Command(TourneysCommand):
    args = '[options] <targetleague sourceleague>'
    help = ('Setup new tournaments or add a round to existing ones between two '
            'leagues')
    option_list = TourneysCommand.option_list + (
        make_option('--newround', action='store_true', dest='newround',
                    default=False,
                    help='Add a new round to an existing tournament.'),
        make_option('--numplayers', type='int', dest='numplayers', default=4,
                    help='Number of players per match.'),
        make_option('--nummatches', type='int', dest='nummatches', default=5,
                    help='Number of matches per competition.'),
        make_option('--seed', type='int', dest='seed', default=None,
                    help='Seed for random number generator.'),
    )

    def getTournamentName(self, targetteam, sourceleague):
        return '%s_%s__%s_tourney' % (targetteam.attribute.name,
                                      'pos' if targetteam.positive else 'neg',
                                      sourceleague.name)

    def cleanTournaments(self, targetleague, sourceleague, num_players,
                         num_matches):
        """Verify clean environment for tournaments between leagues"""
        for league in [targetleague, sourceleague]:
            # verify attributes
            num_attributes = league.attribute_set.count()
            num_rounds = math.log(2*num_attributes)/math.log(num_players)
            if not num_rounds.is_integer():
                raise CommandError(
                    ('Nonintegral number of rounds computed for league `%s`. '
                     'Number of attributes in league must equal (k^n)/2, where '
                     'k > 2 is number of players per match and n > 2 is the '
                     'number of rounds in the tournament.' % league.name)
                )
            # verify teams
            for attribute in league.attribute_set.all():
                if attribute.team_set.count() != 2:
                    raise CommandError(
                        ('Invalid number of teams per attribute for league '
                         '`%s` (must be one team per attribute per sign).') %\
                        league.name
                    )
            # TODO: Perhaps remove this constraint. If so, need to be sure that
            # competition/match creation can handle the num_matches > team_size
            # scenario.
            for team in Team.objects\
                            .filter(attribute__in=league.attribute_set.all()):
                if team.teamplayer_set.count() < num_matches:
                    raise CommandError(
                        ('num_matches=%d cannot be greater than number of '
                         'teamplayers on a team in the league `%s`.') %\
                        (num_matches, league.name)
                    )
        # verify tournaments don't already exist
        for targetteam in\
            Team.objects.filter(attribute__in=targetleague.attribute_set.all()):
            tournament_name = self.getTournamentName(targetteam, sourceleague)
            try:
                tournament = Tournament.objects.get(name=tournament_name)
                raise CommandError(
                    'Tournament `%s` already exists.' % tournament.name
                )
            except Tournament.DoesNotExist:
                pass

    def createMatches(self, tournament, round, num_matches):
        targetteamplayers = list(tournament.targetteam.teamplayer_set.all())
        # randomize target teamplayers
        random.shuffle(targetteamplayers)
        for competition in tournament.competition_set.all():
            teamplayer_lists = {}
            for competitionteam in competition.competitionteam_set.all():
               teamplayers = list(competitionteam.team.teamplayer_set.all())
               # randomize source teamplayers
               random.shuffle(teamplayers)
               teamplayer_lists[competitionteam.pk] = teamplayers
            for i in range(num_matches):
                # create match object
                match = Match(competition=competition,
                              teamplayer=targetteamplayers[i])
                competition.match_set.add(match)
                for competitionteam in competition.competitionteam_set.all():
                    # create competitor object
                    teamplayer = teamplayer_lists[competitionteam.pk].pop()
                    competitor = Competitor(match=match,
                                            competitionteam=competitionteam,
                                            teamplayer=teamplayer)
                    match.competitor_set.add(competitor)

    def createCompetitions(self, tournament, round, num_players):
        if round != 1:
            raise CommandError(
                'Creating competitions for rounds > 1 not implemented'
            )
        # randomize teams
        tournamentteams = list(tournament.tournamentteam_set.all())
        random.shuffle(tournamentteams)
        # create competition objects
        for i in range(len(tournamentteams)/num_players):
            # create competition object
            competition = Competition(tournament=tournament, round=round)
            tournament.competition_set.add(competition)
            # create competitionteam objects
            for j in range(num_players):
                tournamentteam = tournamentteams.pop()
                competitionteam = CompetitionTeam(competition=competition,
                                                  team=tournamentteam.team)
                competition.competitionteam_set.add(competitionteam)

    def createTournamentTeams(self, tournament):
        for attribute in tournament.league.attribute_set.all():
            for team in attribute.team_set.all():
                # create tournamentteam object
                tournamentteam = TournamentTeam(tournament=tournament,
                                                team=team)
                tournament.tournamentteam_set.add(tournamentteam)

    def createTournaments(self, targetleague_name, sourceleague_name,
                          num_players, num_matches):
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
        # verify clean environment
        self.cleanTournaments(targetleague, sourceleague, num_players,
                              num_matches)
        # create tournaments
        for targetteam in\
            Team.objects.filter(attribute__in=targetleague.attribute_set.all()):
            name = self.getTournamentName(targetteam, sourceleague)
            # for now, all tournaments are single-elimination
            ttype = TournamentType.objects.get(name='single-elimination')
            self.stdout.write('Creating tournament: %s' % name)
            tournament = Tournament(
                name=name, ttype=ttype, league=sourceleague,
                targetteam=targetteam, num_players=num_players,
                num_matches=num_matches, round=1, finished=False
            )
            tournament.save()
            # create tournament teams
            self.createTournamentTeams(tournament)
            # create competitions
            self.createCompetitions(tournament, 1, num_players)
            # create matches
            self.createMatches(tournament, 1, num_matches)

    def handle(self, *args, **options):
        # parse command line
        if len(args) != 2:
            raise CommandError('Must provide targetleague and sourceleague')
        targetleague_name = args[0]
        sourceleague_name = args[1]
        newround = options['newround']
        num_players = options['numplayers']
        num_matches = options['nummatches']
        seed = options['seed']

        # seed rng
        if seed is not None:
            random.seed(seed)

        if newround:
            # augment an existing tournaments
            raise CommandError('Modifying existing tournaments not yet '
                               'implemented.')
        else:
            # create new tournaments
            self.createTournaments(targetleague_name, sourceleague_name,
                                   num_players, num_matches)
