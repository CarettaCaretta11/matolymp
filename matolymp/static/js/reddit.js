function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}


function vote(voteButton) {
    let csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    let $voteDiv = $(voteButton).parent().parent();
    let $data = $voteDiv.data();
    let direction_name = $(voteButton).attr('title');
    let vote_value = null;
    if (direction_name === "upvote") {
        vote_value = 1;
    } else if (direction_name === "downvote") {
        vote_value = -1;
    } else {
        return;
    }

    let doPost = $.post('/blog/vote/', {
        what_id: $data.whatId,
        vote_value: vote_value,
    });

    doPost.done(function (response) {
        if (response.error == null) {
            let voteDiff = response.voteDiff;
            let $score = null;
            let $upvoteArrow = null;
            let $downArrow = null;

            // let $medaiDiv = $voteDiv.parent().parent();
            let $votes = $voteDiv.children('div');
            $upvoteArrow = $votes.children('i.fa.fa-chevron-up');
            $downArrow = $votes.children('i.fa.fa-chevron-down');
            $score = $voteDiv.find("a.score:first");


            // update vote elements

            if (vote_value === -1) {
                if ($upvoteArrow.hasClass("upvoted")) { // remove upvote, if any.
                    $upvoteArrow.removeClass("upvoted")
                }
                if ($downArrow.hasClass("downvoted")) { // Canceled downvote
                    $downArrow.removeClass("downvoted")
                } else {                                // new downvote
                    $downArrow.addClass("downvoted")
                }
            } else if (vote_value === 1) {               // remove downvote
                if ($downArrow.hasClass("downvoted")) {
                    $downArrow.removeClass("downvoted")
                }

                if ($upvoteArrow.hasClass("upvoted")) { // if canceling upvote
                    $upvoteArrow.removeClass("upvoted")
                } else {                                // adding new upvote
                    $upvoteArrow.addClass("upvoted")
                }
            } else if (vote_value === 0) {               // voting yourself (that's a no-no)
                if ($upvoteArrow.hasClass("upvoted")) {
                    $upvoteArrow.removeClass("upvoted")
                }
                if ($downArrow.hasClass("downvoted")) {
                    $downArrow.removeClass("downvoted")
                }
            }

            // update score element
            let scoreInt = parseInt($score.text());
            $score.text(scoreInt += voteDiff);
        }
    });
}


function submitEvent(event, form) {
    event.preventDefault();
    let $form = form;
    let data = $form.data();
    let url = $form.attr("action");
    let commentContent = $form.find("textarea#commentContent").val();

    let csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });


    if (commentContent.trim().length > 0) {
        let doPost = $.post(url, {
            parentType: data.parentType,
            parentId: data.parentId,
            commentContent: commentContent
        });
        doPost.done(function (response) {
            location.reload();
        });
    }
}

$("#commentForm").submit(function (event) {
    submitEvent(event, $(this));
});

let newCommentForm = '<form id="commentForm" class="form-horizontal"\
                            action="/blog/post/comment/"\
                            data-parent-type="comment"\
                            style="max-width: 800px;">\
                            <fieldset>\
                            <div class="form-group comment-group">\
                                <label for="commentContent" class="col-lg-2 control-label">New comment</label>\
                                <div class="col-lg-10">\
                                    <textarea class="form-control" rows="3" id="commentContent"></textarea>\
                                    <span id="postResponse" class="text-success" style="display: none"></span>\
                                </div>\
                            </div>\
                            <div class="form-group">\
                                <div class="col-lg-10 col-lg-offset-2">\
                                    <button type="submit" class="btn btn-primary">Submit</button>\
                                </div>\
                            </div>\
                        </fieldset>\
                    </form>';

$('a[name="replyButton"]').click(function () {
    let $mediaBody = $(this).parent().parent().parent();
    if ($mediaBody.find('#commentForm').length === 0) {
        $mediaBody.parent().find(".reply-container:first").append(newCommentForm);
        let $form = $mediaBody.find('#commentForm');
        $form.data('parent-id', $mediaBody.parent().data().parentId);
        $form.submit(function (event) {
            submitEvent(event, $(this));
        });
    } else {
        $commentForm = $mediaBody.find('#commentForm:first');
        if ($commentForm.attr('style') == null) {
            $commentForm.css('display', 'none')
        } else {
            $commentForm.removeAttr('style')
        }
    }

});

function confirmDelete() {
    if (confirm("Are you sure you want to delete this post?")) {
      document.getElementById("deleteForm").submit();
    } else {
      event.preventDefault();
    }
}
