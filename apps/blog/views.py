from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponseBadRequest, Http404, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.template.defaulttags import register

from .forms import SubmissionForm
from .models import Submission, Comment, Vote
from apps.user.utils.helpers import post_only
from apps.user.models import User


@register.filter
def get_item(dictionary, key):  # pragma: no cover
    """
    Needed because there's no built-in .get in django templates
    when working with dictionaries. Used for getting values from
    comment_votes dictionary in comment.html template using comment
    IDs.

    :param dictionary: python dictionary
    :param key: valid dictionary key type
    :return: value of that key or None
    """
    return dictionary.get(key)


def frontpage(request):
    """
    Serves frontpage and all additional submission listings
    with maximum of 25 submissions per page.
    """

    all_submissions = Submission.objects.order_by("-timestamp").all()
    paginator = Paginator(all_submissions, 25)

    page = request.GET.get("page", 1)
    try:
        submissions = paginator.page(page)
    except PageNotAnInteger:
        raise Http404
    except EmptyPage:
        submissions = paginator.page(paginator.num_pages)

    return render(request, "frontpage.html", {"submissions": submissions})


def about(request):
    """
    Serves about page.
    """

    return render(request, "about.html")


@login_required(login_url="/login/")
def comments(request, thread_id):
    """
    Handles comment view when user opens the thread.
    On top of serving all comments in the thread it will
    also return all votes user made in that thread
    so that we can easily update comments in template
    and display via css whether user voted or not.

    :param thread_id: Thread ID as it's stored in database
    :type thread_id: int
    """

    this_submission = get_object_or_404(Submission, id=thread_id)
    thread_comments = Comment.objects.filter(submission=this_submission)

    if request.user.is_authenticated:
        try:
            user = request.user
        except User.DoesNotExist:
            user = None
    else:
        user = None

    if user:
        if request.method == "POST" and this_submission.author == user:
            pass

    comment_votes = {}

    if user:
        try:
            user_thread_votes = Vote.objects.filter(user=user, submission=this_submission)

            for vote in user_thread_votes:
                comment_votes[vote.comment.id] = vote.value  # according to vote value, we change the color of arrows
        except:
            pass

    return render(
        request,
        "comments.html",
        {
            "submission": this_submission,
            "comments": thread_comments,
            "comment_votes": comment_votes,
        },
    )


@post_only
def post_comment(request):
    if not request.user.is_authenticated:
        return JsonResponse({"msg": "You need to log in to post new comments."})

    parent_type = request.POST.get("parentType", None)
    parent_id = request.POST.get("parentId", None)
    content = request.POST.get("commentContent", None)

    if not all([parent_id, parent_type]) or parent_type not in ["comment", "submission"] or not parent_id.isdigit():
        return HttpResponseBadRequest()

    if not content:
        return JsonResponse({"msg": "You have to write something."})
    author = request.user
    parent_object = None
    try:  # try and get comment or submission we're voting on
        if parent_type == "comment":
            parent_object = Comment.objects.get(id=parent_id)
        elif parent_type == "submission":
            parent_object = Submission.objects.get(id=parent_id)

    except (Comment.DoesNotExist, Submission.DoesNotExist):
        return HttpResponseBadRequest()

    comment = Comment.create(author=author, content=content, parent=parent_object)

    comment.save()
    return JsonResponse({"msg": "Your comment has been posted."})


@post_only
def vote(request):
    vote_object_id = request.POST.get("what_id", None)

    # The value of the vote we're writing to the vote object (with id=vote_object_id), -1 or 1
    # Passing the same value twice will cancel the vote i.e. set it to 0
    new_vote_value = request.POST.get("vote_value", None)

    # By how much we'll change the score, used to modify score on the fly
    # client side by the javascript instead of waiting for a refresh.
    vote_diff = 0

    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    else:
        user = request.user

    try:  # If the vote value isn't an integer that's equal to -1 or 1
        # the request is bad and we can not continue.
        if not (new_vote_value.isdigit() or (new_vote_value.startswith("-") and new_vote_value[1:].isdigit())):
            raise ValueError("Not an integer value for the vote!")

        new_vote_value = int(new_vote_value)

        if new_vote_value not in [-1, 1]:
            raise ValueError("Wrong value for the vote!")

    except Exception as e:
        return HttpResponseBadRequest("Wrong value for the vote!")

    # if one of the objects is None, 0 or some other bool(value) == False value, it's a bad request
    if not all([vote_object_id, new_vote_value]):
        return HttpResponseBadRequest("Not all values were provided!")

    # Try and get the existing vote for this object, if it exists.
    try:
        vote = Vote.objects.get(comment=Comment.objects.get(id=vote_object_id), user=user)

    except Vote.DoesNotExist:
        # Create a new vote and that's it.
        vote = Vote.create(user=user, comment=Comment.objects.get(id=vote_object_id), vote_value=new_vote_value)
        vote.save()
        vote_diff = new_vote_value
        return JsonResponse({"error": None, "voteDiff": vote_diff})

    # User already voted on this item, this means the vote is either
    # being canceled (same value) or changed (different new_vote_value)
    if vote.value == new_vote_value:
        # canceling vote
        vote_diff = vote.cancel_vote()
        if not vote_diff:  # in case vote.vote_value is not -1 or 1 (potentially 0)
            return HttpResponseBadRequest("Something went wrong while canceling the vote")
    else:
        # changing vote
        vote_diff = vote.change_vote(new_vote_value)
        if not vote_diff:
            return HttpResponseBadRequest("Wrong values for old/new vote combination")

    return JsonResponse({"error": None, "voteDiff": vote_diff})


@login_required(login_url="/login/")
def submit(request):
    """
    Handles new submission.
    """

    if not request.user.is_staff:
        return HttpResponseForbidden()

    submission_form = SubmissionForm()

    if request.method == "POST":
        submission_form = SubmissionForm(request.POST)
        if submission_form.is_valid():
            submission = submission_form.save(commit=False)
            submission.author = request.user
            submission.author_name = request.user.username
            submission.save()
            messages.success(request, "Submission created")
            return redirect("/blog/comments/{}".format(submission.id))

    return render(request, "submit.html", {"form": submission_form})


@login_required(login_url="/login/")
def update_submission(request, thread_id):
    """
    Handles update of submission.
    """

    submission = get_object_or_404(Submission, id=thread_id)

    if request.user != submission.author:
        return HttpResponseForbidden()

    submission_form = SubmissionForm(instance=submission)

    if request.method == "POST":
        submission_form = SubmissionForm(request.POST, instance=submission)
        if submission_form.is_valid():
            submission = submission_form.save(commit=False)
            submission.save()
            messages.success(request, "Submission updated")
            return redirect("/blog/comments/{}".format(submission.id))

    return render(request, "update_submission.html", {"form": submission_form, "thread_id": thread_id})


@post_only
def delete_submission(request, thread_id):
    """
    Handles deletion of submission.
    """

    submission = get_object_or_404(Submission, id=thread_id)

    if not request.user.is_authenticated:
        return redirect("/login/?next=" + reverse("apps.blog:delete_post", args=(thread_id,)))

    if request.user != submission.author:
        return HttpResponseForbidden()

    submission.delete()
    messages.success(request, "Submission deleted")
    return redirect("frontpage")
