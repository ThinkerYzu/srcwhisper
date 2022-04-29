from django.db import models
from django.contrib.auth.models import User as DJUser

# Create your models here.
class Discussion(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=128)
    description = models.TextField()
    user = models.ForeignKey(DJUser,
                             on_delete=models.PROTECT)
    publish_time = models.DateTimeField()
    pass

class DiscussionHistory(models.Model):
    id = models.AutoField(primary_key=True)
    discussion = models.ForeignKey('Discussion',
                                   on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    description = models.TextField()
    publish_time = models.DateTimeField()
    pass

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    discussion = models.ForeignKey('Discussion',
                                   on_delete=models.CASCADE)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True)

    user = models.ForeignKey(DJUser,
                             on_delete=models.PROTECT)

    filename = models.ForeignKey('File', on_delete=models.PROTECT)
    lineno = models.IntegerField()

    content = models.TextField()
    publish_time = models.DateTimeField()
    last_modified = models.DateTimeField()
    pass

class CommentHistory(models.Model):
    id = models.AutoField(primary_key=True)
    comment = models.ForeignKey('Comment',
                                on_delete=models.CASCADE)
    content = models.TextField()
    publish_time = models.DateTimeField()
    pass

class File(models.Model):
    id = models.AutoField(primary_key=True)
    path = models.CharField(max_length=256, unique=True)
    pass

class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50)
    token = models.CharField(max_length=128)
    pass
