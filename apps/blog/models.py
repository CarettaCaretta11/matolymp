from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from .utils.model_utils import ContentTypeAware, MttpContentTypeAware
from apps.user.models import User

from django.utils import timezone


class AuthornameField:
    def __init__(self):
        self._author_name = None

    @property
    def author_name(self):
        try:
            name = self.author.username
        except Exception:
            name = "deleted user"
        return name

    @author_name.setter
    def author_name(self, value):
        self._author_name = value

    @author_name.deleter
    def author_name(self):
        del self._author_name


class Submission(ContentTypeAware, AuthornameField):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=250)
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    modified = models.BooleanField(default=False)
    updated = models.DateTimeField(null=True, blank=True)
    comment_count = models.IntegerField(default=0)

    @property
    def comments_url(self):
        return "/blog/comments/{}".format(self.id)

    def __unicode__(self):
        return "<Submission:{}>".format(self.id)


class Comment(MttpContentTypeAware, AuthornameField):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, null=True)
    parent = TreeForeignKey(
        "self", on_delete=models.SET_NULL, related_name="children", null=True, blank=True, db_index=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ups = models.IntegerField(default=0)
    downs = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    content = models.TextField(blank=True)

    class MPTTMeta:
        order_insertion_by = ["-score"]

    @classmethod
    def create(cls, author, content, parent):
        """
        Create a new comment instance. If the parent is submisison
        update comment_count field and save it.
        If parent is comment post it as child comment
        :param author: User instance
        :type author: User
        :param content: Raw comment text
        :type content: str
        :param parent: Comment or Submission that this comment is child of
        :type parent: Comment | Submission
        :return: New Comment instance
        :rtype: Comment
        """

        comment = cls(author=author, author_name=author.username, content=content)

        if isinstance(parent, Submission):
            submission = parent
            comment.submission = submission
        elif isinstance(parent, Comment):
            submission = parent.submission
            comment.submission = submission
            comment.parent = parent
        else:
            return
        submission.comment_count += 1
        submission.save()

        return comment

    def __unicode__(self):
        return "<Comment:{}>".format(self.id)


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # who voted
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, null=True)  # under which submission
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True)  # which comment
    value = models.IntegerField(default=0)  # 0, 1 or -1 ( 0 if no vote or cancelled vote )

    @classmethod
    def create(cls, user, comment, vote_value):
        """
        Create a new vote object and return it.
        It will also update the ups/downs/score fields in the
        comment instance and save it.

        :param user: User instance
        :type user: User
        :param comment: Comment the vote is cast on
        :type comment: Comment
        :param vote_value: Value of the vote
        :type vote_value: int
        :return: new Vote instance
        :rtype: Vote
        """

        if cls.objects.filter(user=user, comment=comment).exists():
            vote = cls.objects.get(user=user, comment=comment)
            vote.value = vote_value
            vote.save()
            return vote

        vote = cls(user=user, comment=comment, value=vote_value)
        submission = comment.submission
        vote.submission = submission
        comment.score += vote_value
        comment.author.karma += vote_value

        if vote_value == 1:
            comment.ups += 1
        elif vote_value == -1:
            comment.downs += 1

        comment.save()
        comment.author.save()

        return vote

    def change_vote(self, new_vote_value):
        if self.value == -1 and new_vote_value == 1:  # down to up
            vote_diff = 2
            self.comment.score += 2
            self.comment.ups += 1
            self.comment.downs -= 1
        elif self.value == 1 and new_vote_value == -1:  # up to down
            vote_diff = -2
            self.comment.score -= 2
            self.comment.ups -= 1
            self.comment.downs += 1
        elif self.value == 0 and new_vote_value == 1:  # canceled vote to up
            vote_diff = 1
            self.comment.ups += 1
            self.comment.score += 1
        elif self.value == 0 and new_vote_value == -1:  # canceled vote to down
            vote_diff = -1
            self.comment.downs += 1
            self.comment.score -= 1
        else:
            return None

        self.comment.author.karma += vote_diff
        self.value = new_vote_value
        self.comment.save()
        self.comment.author.save()
        self.save()

        return vote_diff

    def cancel_vote(self):
        if self.value == 1:
            vote_diff = -1
            self.comment.ups -= 1
            self.comment.score -= 1
        elif self.value == -1:
            vote_diff = 1
            self.comment.downs -= 1
            self.comment.score += 1
        else:
            return None

        self.comment.author.karma += vote_diff
        self.value = 0
        self.save()
        self.comment.save()
        self.comment.author.save()
        return vote_diff
