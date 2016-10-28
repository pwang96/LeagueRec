from __future__ import unicode_literals
import json
from django.db import models
from user.util import process_summoner


class User(models.Model):
    name = models.CharField(max_length=50, default="defaultname")
    verbose_name = models.CharField(max_length=50, default="defaultname")
    rank = models.CharField(max_length=50, default="defaultrank")
    date_accessed = models.DateField(auto_now=True)
    top_5_champs = models.CharField(max_length=300, null=True)
    top_5_played = models.CharField(max_length=300, null=True)
    recommended_champs = models.CharField(max_length=300, null=True)
    champion_vector = models.CharField(max_length=300, null=True)
    summoner_icon = models.CharField(max_length=200, default="none")

    def set_top_5(self, listOf5Champs):
        self.top_5_champs = json.dumps(listOf5Champs)
        self.save()

    def set_top_5_played(self, listOf5Champs):
        self.top_5_played = json.dumps(listOf5Champs)
        self.save()

    def set_recommended_champs(self, listOfRecChamps):
        self.recommended_champs = json.dumps(listOfRecChamps)
        self.save()

    def set_champion_vector(self, vector):
        self.champion_vector = json.dumps(vector)
        self.save()

    def get_top_5(self):
        return json.loads(self.top_5_champs)

    def get_top_5_played(self):
        return json.loads(self.top_5_played)

    def get_recommended_champs(self):
        return json.loads(self.recommended_champs)

    def process(self):
        top5played, recs, self.summoner_icon, self.rank = process_summoner(self.name)
        self.set_top_5_played(top5played)
        self.set_recommended_champs(recs)

    def __str__(self):
        return self.name


def clear_cache():
    User.objects.all().delete()