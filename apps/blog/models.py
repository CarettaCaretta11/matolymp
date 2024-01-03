from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey
from .utils.model_utils import ContentTypeAware, MttpContentTypeAware
from apps.user.models import User


class Submission(ContentTypeAware):
    _author_name = None
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=250)
    content = models.TextField(max_length=5000, blank=True)
    ups = models.IntegerField(default=0)
    downs = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)
    comment_count = models.IntegerField(default=0)

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
        del self.author_name

    @property
    def comments_url(self):
        return "/blog/comments/{}".format(self.id)

    def __unicode__(self):
        return "<Submission:{}>".format(self.id)


class Comment(MttpContentTypeAware):
    author_name = models.CharField(null=False, max_length=12)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    parent = TreeForeignKey(
        "self", on_delete=models.SET_NULL, related_name="children", null=True, blank=True, db_index=True
    )
    timestamp = models.DateTimeField(default=timezone.now)
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
        :param raw_comment: Raw comment text
        :type raw_comment: str
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
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)  # under which submission
    vote_object_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    vote_object_id = models.PositiveIntegerField()
    vote_object = GenericForeignKey("vote_object_type", "vote_object_id")  # submission itself or a comment under it
    value = models.IntegerField(default=0)  # 0, 1 or -1 ( 0 if cancel_vote() )

    @classmethod
    def create(cls, user, vote_object, vote_value):
        """
        Create a new vote object and return it.
        It will also update the ups/downs/score fields in the
        vote_object instance and save it.

        :param user: User instance
        :type user: User
        :param vote_object: Instance of the object the vote is cast on
        :type vote_object: Comment | Submission
        :param vote_value: Value of the vote
        :type vote_value: int
        :return: new Vote instance
        :rtype: Vote
        """

        if isinstance(vote_object, Submission):
            submission = vote_object
            vote_object.author.post_karma += vote_value
        else:
            submission = vote_object.submission
            vote_object.author.comment_karma += vote_value

        vote = cls(user=user, vote_object=vote_object, value=vote_value)

        vote.submission = submission
        # the value for new vote will never be 0
        # that can happen only when removing up/down vote.
        vote_object.score += vote_value
        if vote_value == 1:
            vote_object.ups += 1
        elif vote_value == -1:
            vote_object.downs += 1

        vote_object.save()
        vote_object.author.save()

        return vote

    def change_vote(self, new_vote_value):
        if self.value == -1 and new_vote_value == 1:  # down to up
            vote_diff = 2
            self.vote_object.score += 2
            self.vote_object.ups += 1
            self.vote_object.downs -= 1
        elif self.value == 1 and new_vote_value == -1:  # up to down
            vote_diff = -2
            self.vote_object.score -= 2
            self.vote_object.ups -= 1
            self.vote_object.downs += 1
        elif self.value == 0 and new_vote_value == 1:  # canceled vote to up
            vote_diff = 1
            self.vote_object.ups += 1
            self.vote_object.score += 1
        elif self.value == 0 and new_vote_value == -1:  # canceled vote to down
            vote_diff = -1
            self.vote_object.downs += 1
            self.vote_object.score -= 1
        else:
            return None

        if isinstance(self.vote_object, Submission):
            self.vote_object.author.post_karma += vote_diff
        else:
            self.vote_object.author.comment_karma += vote_diff

        self.value = new_vote_value
        self.vote_object.save()
        self.vote_object.author.save()
        self.save()

        return vote_diff

    def cancel_vote(self):
        if self.value == 1:
            vote_diff = -1
            self.vote_object.ups -= 1
            self.vote_object.score -= 1
        elif self.value == -1:
            vote_diff = 1
            self.vote_object.downs -= 1
            self.vote_object.score += 1
        else:
            return None

        if isinstance(self.vote_object, Submission):
            self.vote_object.author.post_karma += vote_diff
        else:
            self.vote_object.author.comment_karma += vote_diff

        self.value = 0
        self.save()
        self.vote_object.save()
        self.vote_object.author.save()
        return vote_diff
