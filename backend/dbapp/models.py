from django.db import models

class AppUser(models.Model):  # ← User 대신 AppUser로
    id = models.AutoField(primary_key=True)  # IntegerField → AutoField 권장
    name = models.CharField(max_length=100)
    main_role = models.CharField(max_length=50, null=True, blank=True)
    sub_role = models.CharField(max_length=50, null=True, blank=True)
    intro = models.TextField(null=True, blank=True)
    skills = models.JSONField(null=True, blank=True)
    keywords = models.JSONField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    participation = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    has_reward = models.BooleanField(default=False)

    class Meta:
        db_table = 'users'
        managed = True   # ← SQLite 개발용으로 True
        verbose_name = "User"
        verbose_name_plural = "Users"


class Team(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    leader = models.ForeignKey(AppUser, db_column='leader_id', on_delete=models.CASCADE)
    matching_type = models.CharField(max_length=10)
    is_finalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'teams'
        managed = True


class TeamMember(models.Model):
    id = models.AutoField(primary_key=True)
    team = models.ForeignKey(Team, db_column='team_id', on_delete=models.CASCADE)
    user = models.ForeignKey(AppUser, db_column='user_id', on_delete=models.CASCADE)
    role = models.CharField(max_length=10, null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'team_members'
        managed = True
        unique_together = (('team', 'user'),)


class Feedback(models.Model):
    id = models.AutoField(primary_key=True)
    team = models.ForeignKey(Team, db_column='team_id', on_delete=models.CASCADE)
    user = models.ForeignKey(AppUser, db_column='user_id', on_delete=models.CASCADE)
    is_agree = models.BooleanField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'feedbacks'
        managed = True
        unique_together = (('team', 'user'),)


class WaitingUser(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=100, unique=True)
    skills = models.JSONField()
    main_role = models.CharField(max_length=100)
    sub_role = models.CharField(max_length=100, null=True, blank=True)
    keywords = models.JSONField()
    has_reward = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'waiting_users'
        managed = True


class Rewarded(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(AppUser, db_column='user_id', on_delete=models.CASCADE)
    is_rewarded = models.BooleanField(null=True)
    granted_at = models.DateTimeField(auto_now_add=True)
    user_name = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'rewarded'
        managed = True
