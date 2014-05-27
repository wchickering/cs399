import datetime
import os
import random
import math

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

# analogous to a retailer
class League(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    mediadir = models.CharField(max_length=20, verbose_name='Media Directory')
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['name']
    #####
    # actions
    ######
    def create_teams(self, teamsize):
        """Create two teams per attribute, one positive, the other negative."""
        self.clean_teams()
        for attribute in self.attribute_set.all():
           for positive in [True, False]:
               team_name = self.get_team_name(attribute, positive)
               # create new team object
               team = Team(name=team_name, attribute=attribute,
                           positive=positive)
               attribute.team_set.add(team)
               # get top players for attribute
               top_playerattributes = attribute.playerattribute_set\
                   .order_by('-value' if positive else 'value')[:teamsize]
               for top_pa in top_playerattributes:
                   # create teamplayer object
                   teamplayer = TeamPlayer(team=team, player=top_pa.player)
                   team.teamplayer_set.add(teamplayer)
    def get_team_name(self, attribute, positive):
        """Generate a name for a new team."""
        return '%s_%s_team' % (attribute.name, 'pos' if positive else 'neg')
    def clean_teams(self):
        """
        Validate models prior to creating teams.
        For now, simply require that no teams already exist for league.
        """
        if Team.objects.filter(attribute__league=self).exists():
            raise ValidationError('Teams already exist for %s' % self)
    def create_tournaments(self, targetleague, tournamenttype, num_players,
                           num_matches):
        """Create tournaments targeting TARGETLEAGUE."""
        self.clean_tournaments(targetleague, tournamenttype, num_players,
                               num_matches)
        for targetteam in Team.objects\
                              .filter(attribute__league=targetleague):
            name = self.get_tournament_name(targetteam)
            tournament = Tournament(
                name=name, ttype=tournamenttype, league=self,
                targetteam=targetteam, num_players=num_players,
                num_matches=num_matches, round=1, finished=False
            )
            self.tournament_set.add(tournament)
            # create tournament teams
            for team in Team.objects.filter(attribute__league=self):
                tournamentteam = TournamentTeam(tournament=tournament,
                                                team=team)
                tournament.tournamentteam_set.add(tournamentteam)
            # create competitions
            tournament.create_competitions()
    def get_tournament_name(self, targetteam):
        """Generate a name for a new tournament."""
        return '%s_%s__%s_tourney' % (targetteam.attribute.name,
                                      'pos' if targetteam.positive else 'neg',
                                      self.name)
    def clean_tournaments(self, targetleague, tournamenttype, num_players,
                          num_matches):
        """Validate models prior to creating tournaments."""
        if tournamenttype.name == 'single-elimination':
            # verify attributes
            num_attributes = self.attribute_set.count()
            num_rounds = math.log(2*num_attributes)/math.log(num_players)
            if not num_rounds.is_integer():
                raise ValidationError(
                    ('Nonintegral number of rounds computed for %s. For '
                     'single-elimination tournaments, number of attributes in '
                     'league must equal (k^n)/2, where k > 2 is number of '
                     'players per match and n > 2 is the number of rounds in '
                     'the tournament.') % self
                )
        else:
            raise ValidationError(
                'Unsupported tournament type: %s' % tournamenttype
            )
        # verify tournaments don't already exist
        for targetteam in Team.objects\
                              .filter(attribute__league=targetleague):
            tournament_name = self.get_tournament_name(targetteam)
            try:
                tournament = Tournament.objects.get(name=tournament_name)
                raise ValidationError(
                    'Tournament `%s` already exists.' % tournament
                )
            except Tournament.DoesNotExist:
                pass

# analogous to a concept
class Attribute(models.Model):
    league = models.ForeignKey(League)
    name = models.CharField(max_length=100)
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['league', 'name']
        unique_together = ('league', 'name')

# analogous to a product
class Player(models.Model):
    league = models.ForeignKey(League)
    code = models.CharField(max_length=100)
    url = models.CharField(max_length=200, verbose_name='URL')
    description = models.TextField()
    def image_path(instance, filename):
       return os.path.join(instance.league.mediadir, filename)
    image = models.ImageField(upload_to=image_path)
    def __unicode__(self):
        return self.description
    def url_tag(self):
        return '<a href="http://%s">Web Link</a>' % self.url
    url_tag.short_description = 'URL'
    url_tag.allow_tags = True
    def image_tag(self):
        return '<img src="%s"/>' % self.image.url
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True
    # a bit sketchy (couples model and admin app)
    def admin_image_tag(self):
        url = reverse('admin:%s_%s_change' % (self._meta.app_label,
                                              self._meta.module_name),
                      args=(self.id,))
        return '<a href="%s">%s</a>' % (url, self.image_tag())
    admin_image_tag.short_description = 'Image'
    admin_image_tag.allow_tags = True
    class Meta:
        ordering = ['league', 'code']
        unique_together = ('league', 'code')

# analogous to a productconcept
class PlayerAttribute(models.Model):
    player = models.ForeignKey(Player)
    attribute = models.ForeignKey(Attribute)
    value = models.FloatField()
    def __unicode__(self):
        return '%s : %s' % (unicode(self.player), unicode(self.attribute))
    def league(self):
        return self.attribute.league
    class Meta:
        ordering = ['player', 'attribute']
        unique_together = ('player', 'attribute')
    def clean(self):
        if self.player.league != self.attribute.league:
            raise ValidationError(
                'Player League `%s` not equal to Attribute League `%s`' % (
                    self.player.league,
                    self.attribute.league
                )
            )

# an attribute (i.e. concept) in the context of tournaments
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    attribute = models.ForeignKey(Attribute)
    positive = models.BooleanField(default=True, verbose_name='Positive?')
    def __unicode__(self):
        return self.name
    def league(self):
        return self.attribute.league
    def playercount(self):
        return self.teamplayer_set.count()
    playercount.short_description = 'Player Count'
    class Meta:
        ordering = ['name', 'attribute']

# a player (i.e. product) in the context of a team
class TeamPlayer(models.Model):
    team = models.ForeignKey(Team)
    player = models.ForeignKey(Player)
    def __unicode__(self):
        return '%s : %s' % (unicode(self.team), unicode(self.player))
    def league(self):
        return self.team.attribute.league
    def image_tag(self):
        return self.player.image_tag()
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True
    def admin_image_tag(self):
        return self.player.admin_image_tag()
    admin_image_tag.short_description = 'Image'
    admin_image_tag.allow_tags = True
    class Meta:
        ordering = ['team', 'player']
        unique_together = ('team', 'player')
    def clean(self):
        if self.team.attribute.league != self.player.league:
            raise ValidationError(
                'Team League `%s` not equal to Player League `%s`' % (
                    self.team.attribute.league,
                    self.player.league
                )
            )

class TournamentType(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['name']

# analogous to a MTurk job
class Tournament(models.Model):
    name = models.CharField(max_length=100, unique=True)
    ttype = models.ForeignKey(TournamentType, verbose_name='Tournament Type')
    # league within which teams will compete
    league = models.ForeignKey(League)
    # target team being matched to
    targetteam = models.ForeignKey(Team, related_name='targetteam',
                                   verbose_name='Target Team')
    num_players = models.PositiveSmallIntegerField()
    num_matches = models.PositiveSmallIntegerField()
    round = models.PositiveSmallIntegerField(default=1)
    finished = models.BooleanField(default=False)
    def __unicode__(self):
        return self.name
    def targetattribute(self):
        return self.targetteam.attribute
    targetattribute.short_description = 'Target Attribute'
    def targetleague(self):
        return self.targetattribute().league
    targetleague.short_description = 'Target League'
    class Meta:
        ordering = ['name']
    ######
    # actions
    ######
    def create_competitions(self):
        """Create initial competitions for tournament."""
        if self.round != 1:
            raise ValidationError(
                ('Call to crate initial competitions for tournament `%s` with '
                 'round != 1') % self
            )
        if self.competition_set.exists():
            raise ValidationError(
                ('Duplicate call to create initial competitions for tournament '
                 '`%s`') % self
            )
        # randomize teams
        tournamentteams = list(self.tournamentteam_set.all())
        random.shuffle(tournamentteams)
        if self.ttype.name == 'single-elimination':
            # create competition objects
            for i in range(len(tournamentteams)/self.num_players):
                # create competition object
                competition = Competition(tournament=self,
                                          round=self.round)
                self.competition_set.add(competition)
                # create competitionteam objects
                for j in range(self.num_players):
                    tournamentteam = tournamentteams.pop()
                    competitionteam = CompetitionTeam(competition=competition,
                                                      team=tournamentteam.team)
                    competition.competitionteam_set.add(competitionteam)
                # create matches
                competition.create_matches()
        else:
            raise ValidationError(
                'Unsupported tournament type: `%s`' % self.ttype
            )
    def advance(self):
        """Advance to next round, creating new competitions, etc.."""
        if self.ttype.name == 'single-elimination':
            all_competitions_finished = True
            winners = []
            for competition in self.competition_set.filter(round=self.round):
                if not competition.finished:
                    # tournament round not complete
                    return
                winners.append(competition.get_winner())
            if len(winners) == 1:
                # tournament finished
                self.finished = True
                self.save()
                return
            random.shuffle(winners)
            # create competition objects
            for i in range(len(winners)/self.num_players):
                # create competition object
                competition = Competition(tournament=self,
                                          round=self.round + 1)
                self.competition_set.add(competition)
                # create competitionteam objects
                for j in range(self.num_players):
                    team = winners.pop()
                    competitionteam = CompetitionTeam(competition=competition,
                                                      team=team)
                    competition.competitionteam_set.add(competitionteam)
                # create matches
                competition.create_matches()
            self.round += 1
            self.save()
        else:
            raise ValidationError(
                'Unsupported tournament type: `%s`' % self.ttype
            )
    #####
    # validation
    ######
    def clean(self):
        if self.round == 0:
            raise ValidationError('Round must be finite.')
        # TODO: Perhaps we want to lift this constraint in order to run tests in
        # which we match attributes against themselves
        if self.league == self.targetteam.attribute.league:
            raise ValidationError(
                'Source League `%s` is equal to Target Team League' % (
                    self.league,
                )
            )

# a team (i.e. concept) in the context of a tournament
class TournamentTeam(models.Model):
    tournament = models.ForeignKey(Tournament)
    team = models.ForeignKey(Team)
    def __unicode__(self):
        return '%s : %s' % (unicode(self.tournament), unicode(self.team))
    class Meta:
        ordering = ['tournament', 'team']
        unique_together = ('tournament', 'team')
    def clean(self):
        if self.tournament.league != self.team.attribute.league:
            raise ValidationError(
                'Tournament League `%s` not equal to Team League `%s`' % (
                    self.tournament.league,
                    self.team.attribute.league
                )
            )

# a competition between multiple source concepts to match a target concept
class Competition(models.Model):
    tournament = models.ForeignKey(Tournament)
    round = models.PositiveSmallIntegerField(default=1)
    finished = models.BooleanField(default=False, verbose_name='Finished?')
    next_competition = models.ForeignKey('self', null=True, blank=True)
    def __unicode__(self):
        return '%s (Rnd %d)' % (unicode(self.tournament), self.round)
    def league(self):
        return self.tournament.league
    def team(self):
        return self.tournament.targetteam
    team.short_description = 'Target Team'
    def attribute(self):
        return self.tournament.targetteam.attribute
    attribute.short_description = 'Team Attribute'
    def targetleague(self):
        return self.tournament.targetleague()
    targetleague.short_description = 'Target League'
    class Meta:
        ordering = ['tournament', 'round']
    ######
    # actions
    ######
    def create_matches(self):
        """Create matches between competitionteams."""
        targetteamplayers =\
            list(self.tournament.targetteam.teamplayer_set.all())
        # randomize target teamplayers
        random.shuffle(targetteamplayers)
        teamplayer_lists = {}
        for competitionteam in self.competitionteam_set.all():
           teamplayers = list(competitionteam.team.teamplayer_set.all())
           # randomize source teamplayers
           random.shuffle(teamplayers)
           teamplayer_lists[competitionteam.pk] = teamplayers
        for i in range(self.tournament.num_matches):
            # create match object
            match = Match(competition=self,
                          teamplayer=targetteamplayers[i%len(targetteamplayers)])
            self.match_set.add(match)
            for competitionteam in self.competitionteam_set.all():
                # create competitor object
                teamplayer = teamplayer_lists[competitionteam.pk].pop()
                competitor = Competitor(match=match,
                                        competitionteam=competitionteam,
                                        teamplayer=teamplayer)
                match.competitor_set.add(competitor)
    def score(self):
        """
        Determine and set scores for competition. If all matches in a
        competition have finished=True, then competition.finished will be set to
        True.
        """
        scores = {}
        all_matches_finished = True
        for match in self.match_set.all():
            if not match.finished:
                all_matched_finished = False
                continue
            match.score()
            for competitor in match.competitor_set.all():
                if competitor.competitionteam.pk not in scores:
                    scores[competitor.competitionteam.pk] = []
                scores[competitor.competitionteam.pk]\
                    .append(competitor.score)
        if all_matches_finished:
            for competitionteam_pk, match_scores in scores.items():
                competitionteam = CompetitionTeam.objects\
                                                 .get(pk=competitionteam_pk)
                competitionteam.score = sum(match_scores)/len(match_scores)
                competitionteam.save()
            self.finished = True
            self.save()
    def get_winner(self):
        """
        Return the winning team, randomly breaking ties. If competition has
        finished=False, returns None.
        """
        if not self.finished:
            return None
        candidates = []
        for competitionteam in self.competitionteam_set.order_by('-score'):
            if not candidates or \
                competitionteam.score == candidates[-1].score:
                candidates.append(competitionteam)
            else:
                break
        return random.choice(candidates).team
    #####
    # validation
    ######
    def clean(self):
        if self.next_competition is not None:
            if self.next_competition.tournament != self.tournament:
                raise ValidationError(
                    ('Next competition tournament `%s` not equal to this '
                     'competition tournament `%s`') % (
                        self.next_competition.tournament,
                        self.tournament
                    )
                )
            if self.next_competition.round != self.round + 1:
                raise ValidationError(
                    ('Next competition round %u not equal to this competition '
                     'round %u plus one') % (
                        self.next_competition.round,
                        self.round
                    )
                )
        if self.finished:
            if self.competitionteam_set.count() != self.tournament.num_players:
                raise ValidationError(
                    ('Number of competitionteams not equal to '
                     'tournament.num_player for finished competition %d') %\
                     self.pk
                )
            if self.match_set.count() != self.tournament.num_matches:
                raise ValidationError(
                    ('Number of matches not equal to tournament.num_matches '
                     'for finished competition %d') % self.pk
                )

# a team (i.e. concept) in the context of a competition
class CompetitionTeam(models.Model):
    competition = models.ForeignKey(Competition)
    team = models.ForeignKey(Team)
    score = models.FloatField(null=True, blank=True)
    def __unicode__(self):
        return '%s : %s' % (unicode(self.competition), unicode(self.team))
    class Meta:
        ordering = ['competition', 'team']
        unique_together = ('competition', 'team')
    def clean(self):
        if not self.competition.tournament.tournamentteam_set\
                                          .filter(team=self.team).exists():
            raise ValidationError(
                'Team `%s` not in Tournament `%s`' % (
                    self.team,
                    self.competition.tournament
                )
            )

# analogous to a task in MTurk
# a competition consists of several matches
class Match(models.Model):
    competition = models.ForeignKey(Competition)
    teamplayer = models.ForeignKey(TeamPlayer,
                                   verbose_name='Target Team Player')
    finished = models.BooleanField(default=False, verbose_name='Finished?')
    def __unicode__(self):
        return '%s : %s' % (unicode(self.competition), unicode(self.teamplayer))
    def image_tag(self):
        return self.teamplayer.image_tag()
    image_tag.short_description = 'Target Image'
    image_tag.allow_tags = True
    def admin_image_tag(self):
        return self.teamplayer.admin_image_tag()
    admin_image_tag.short_description = 'Target Image'
    admin_image_tag.allow_tags = True
    class Meta:
        ordering = ['competition', 'teamplayer']
    def score(self):
        """Determine and set scores for match."""
        competitors = self.competitor_set.all()
        num_winners = competitors.filter(winner=True).count()
        if num_winners > 0:
            winner_score = 1.0/num_winners
        else:
            winner_score = 1.0/competitors.count()
        for competitor in competitors:
            if num_winners == 0 or competitor.winner:
                competitor.score = winner_score
            else:
                competitor.score = 0.0
            competitor.save()
    def clean(self):
        if self.competition.tournament.targetteam != self.teamplayer.team:
            raise ValidationError(
                'Competition Team `%s` not equal to TeamPlayer Team `%s`' % (
                    self.competition.tournament.targetteam,
                    self.teamplayer.team
                )
            )
        if self.finished:
            if self.competitor_set.count() !=\
               self.competition.tournament.num_players:
                raise ValidationError(
                    ('Number of competitors not equal to tournament.num_payer '
                     'for finished match %d') % self.pk
                )

# a player (i.e. product) in the context of a match
class Competitor(models.Model):
    match = models.ForeignKey(Match)
    competitionteam = models.ForeignKey(CompetitionTeam,
                                        verbose_name='Competition Team')
    teamplayer = models.ForeignKey(TeamPlayer, verbose_name='Team Player')
    winner = models.NullBooleanField(verbose_name='Winner?')
    score = models.FloatField(null=True, blank=True)
    def __unicode__(self):
        return '%s : %s' % (unicode(self.competitionteam),
                            unicode(self.teamplayer))
    def image_tag(self):
        return self.teamplayer.image_tag()
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True
    def admin_image_tag(self):
        return self.teamplayer.admin_image_tag()
    admin_image_tag.short_description = 'Image'
    admin_image_tag.allow_tags = True
    class Meta:
        ordering = ['match', 'competitionteam', 'teamplayer']
        # no duplicate players or teams in match
        unique_together = (('match', 'competitionteam'),
                           ('match', 'teamplayer'))
    def clean(self):
        if self.match.competition != self.competitionteam.competition:
            raise ValidationError(
                ('Match Competition `%s` not equal to CompetitionTeam '
                 'Competition `%s`') % (
                    self.match.competition,
                    self.competitionteam.competition
                )
            )
        if self.teamplayer.team != self.competitionteam.team:
            raise ValidationError(
                ('TeamPlayer Team `%s` not equal to CompetitionTeam Team '
                 '`%s`') % (
                    self.teamplayer.team,
                    self.competitionteam.team
                )
            )
    
