from django.db import models

class User(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    main_role = models.CharField(max_length=50, null=True)
    sub_role = models.CharField(max_length=50, null=True)
    intro = models.TextField(null=True)
    skills = models.JSONField(null=True)
    keywords = models.JSONField(null=True)
    rating = models.FloatField(null=True)
    participation = models.IntegerField(null=True)
    created_at = models.DateTimeField(null=True)
    has_reward = models.BooleanField(default=False)
    class Meta: managed = False; db_table = 'users'

class Team(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, null=True)
    leader = models.ForeignKey('User', db_column='leader_id', on_delete=models.DO_NOTHING)
    matching_type = models.CharField(max_length=10)
    is_finalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True)
    class Meta: managed = False; db_table = 'teams'

class TeamMember(models.Model):
    id = models.AutoField(primary_key=True)
    team = models.ForeignKey(Team, db_column='team_id', on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, db_column='user_id', on_delete=models.DO_NOTHING)
    role = models.CharField(max_length=10, null=True)
    joined_at = models.DateTimeField(null=True)
    class Meta:
        managed = False
        db_table = 'team_members'
        unique_together = (('team','user'),)

class Feedback(models.Model):
    id = models.AutoField(primary_key=True)
    team = models.ForeignKey(Team, db_column='team_id', on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, db_column='user_id', on_delete=models.DO_NOTHING)
    is_agree = models.BooleanField(null=True)
    created_at = models.DateTimeField(null=True)
    class Meta:
        managed = False
        db_table = 'feedbacks'
        unique_together = (('team','user'),)

class WaitingUser(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=100, unique=True)
    skills = models.JSONField()
    main_role = models.CharField(max_length=100)
    sub_role = models.CharField(max_length=100, null=True)
    keywords = models.JSONField()
    has_reward = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True)
    class Meta:
        managed = False
        db_table = 'waiting_users'
        unique_together = (('user_id',),)

class Rewarded(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, db_column='user_id', on_delete=models.DO_NOTHING)
    is_rewarded = models.BooleanField(null=True)
    granted_at = models.DateTimeField(null=True)
    user_name = models.CharField(max_length=50, null=True)
    class Meta: managed = False; db_table = 'rewarded'
