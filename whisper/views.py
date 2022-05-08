from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import ensure_csrf_cookie
from .srcsvc import SourceService

from .models import File, Discussion, Comment
from .models import DiscussionHistory, CommentHistory
from django.contrib.auth.models import User

import os
import itertools

from pygments import highlight
from pygments.lexers import get_lexer_for_filename, MarkdownLexer
from pygments.formatters import HtmlFormatter

from datetime import datetime

srcs = SourceService()

def get_comments(discussion_id):
    discussion = Discussion.objects.get(id=discussion_id)
    if not discussion:
        return None

    comments = [{'id': cmt.id,
                 'path': cmt.filename.path,
                 'lineno': cmt.lineno,
                 'user': cmt.user.username,
                 'content': cmt.content,
                 'publish_time': cmt.publish_time,
                 'reply_to': cmt.reply_to and cmt.reply_to.id or 0,
                }
                for cmt in discussion.comment_set.all()]
    comments = sorted(comments,
                      key=lambda x: (x['path'], x['lineno']))
    comments = itertools.groupby(comments,
                                 key=lambda x: (x['path'], x['lineno']))
    comments = [list(sorted(grp[1],
                            key=lambda x: ((x['reply_to'] and 1) or 0, x['publish_time'])))
                for grp in comments]
    comments = [{'comment': cmt[0], 'replys': cmt[1:]}
                for cmt in comments]
    comments.sort(key=lambda x: x['comment']['publish_time'])
    return comments

def empty(request):
    discussions = Discussion.objects.order_by('publish_time').reverse()[:settings.EMPTY_MAX_DISCUSSIONS]
    discussions = [{'id': dis.id,
                    'title': dis.title,
                    'author': dis.user.username,
                    'description': dis.description[:200]}
                   for dis in discussions]
    context = {'discussions': discussions}
    template = loader.get_template('whisper/empty.html');
    source = template.render(context, request)
    return source

# site_rel_root is common URL root of source files.
#
# It is whisper/discuss/<ID>/p in a discussion, or whisper/code not in
# a discussion.
def show_view(request, path, site_rel_root, site_cmtpath,
              site_newdiscusspath,
              discussion_id, comments):
    origin = path
    if srcs.is_file(path):
        filename = srcs.get_basename(path)
        path = srcs.get_dirname(path).strip('/')
        try:
            lexer = get_lexer_for_filename(filename)
        except:
            lexer = MarkdownLexer()
            pass
        try:
            formatter = HtmlFormatter(linenos=True,
                                      cssclass="source",
                                      full=True,
                                      linespans='line',
                                      title=filename)
            code = srcs.open_file(origin).read()
            source = highlight(code, lexer, formatter)
        except:
            source = empty(request)
            pass
    else:
        filename = ''
        source = empty(request)
        pass

    return render_view(request, path, site_rel_root, site_cmtpath,
                       site_newdiscusspath,
                       discussion_id, comments, filename, source, origin)

def render_view(request, path, site_rel_root, site_cmtpath,
                site_newdiscusspath,
                discussion_id, comments, filename, source, origin):
    if '_auth_user_id' in request.session:
        user = User.objects.get(pk=request.session['_auth_user_id'])
        username = user.username
    else:
        username = ''
        pass

    # The path related to site_rel_root
    rel_url = srcs.get_rel_url(origin)

    dirs, files, rel_dir = srcs.list(path)
    dirs.sort()
    files.sort()
    template = loader.get_template('whisper/codeview.html')
    context = {
        'comments': comments,
        'subdirectories': dirs,
        'files': files,
        'user': username,
        'source': source,
        'rel_dir': rel_dir,
        'rel_url': rel_url,
        'filename': filename,
        'site_rel_root': site_rel_root,
        'site_cmtpath': site_cmtpath,
        'site_newdiscusspath': site_newdiscusspath,
        'discussion_id': discussion_id,
    }
    if discussion_id:
        dis = Discussion.objects.get(pk=discussion_id)
        context['discussion_title'] = dis.title
        context['discussion_description'] = dis.description
        context['discussion_user'] = dis.user.username
        pass

    return HttpResponse(template.render(context, request))

def add_comment(request, path):
    parts = path.split('/')
    filename = os.path.join(*parts[1:])
    if not srcs.is_file(filename):
        return

    line_no = int(request.POST['line_no'])
    discussion_id = int(request.POST['discussion_id'])
    content = request.POST['content']

    dis = Discussion.objects.get(id=discussion_id)
    try:
        fo = File.objects.get(path=filename)
    except:
        fo = File(path=filename)
        fo.save()
        pass
    existing_cmts = dis.comment_set.filter(filename=fo,
                                            lineno=line_no,
                                            reply_to=None)
    if len(existing_cmts):
        reply_to = existing_cmts[0]
    else:
        reply_to = None
        pass

    user = User.objects.get(id=request.session['_auth_user_id'])
    now = datetime.now()
    cmt = Comment(discussion=dis,
                  reply_to=reply_to,
                  user=user,
                  filename=fo,
                  lineno=line_no,
                  content=content,
                  publish_time=now,
                  last_modified=now)
    cmt.save()

    return HttpResponse('OK:' + str(cmt.id))

def update_comment(request, path):
    parts = path.split('/')
    cmt_id = int(parts[1])

    cmt = Comment.objects.get(pk=cmt_id)

    user = cmt.user
    user_id = int(request.session['_auth_user_id'])
    if user.id != user_id:
        raise 'Invalid user ID'

    content = request.POST['content']
    if content == cmt.content:
        return HttpResponse('OK')

    chist = CommentHistory(comment=cmt,
                           content=cmt.content,
                           publish_time=cmt.last_modified)
    cmt.content = content
    cmt.last_modified = datetime.now()

    chist.save()
    cmt.save()

    return HttpResponse('OK')

def new_discussion(request):
    form = loader.get_template('whisper/new_discussion.html').render({}, request)
    return HttpResponse(form)

def create_discussion(request):
    title = request.POST['title']
    if len(title) > 128:
        title = title[:128]
        pass
    description = request.POST['description']
    if len(description) > 512:
        description = description[:512]
        pass
    user = User.objects.get(id=request.session['_auth_user_id'])
    discussion = Discussion(title=title, description=description,
                            user=user,
                            publish_time=datetime.now())
    discussion.save()

    return redirect('/whisper/discuss/' + str(discussion.id) + '/p/')

def update_discussion(request, path):
    discussion_id = int(path.split('/')[1])
    discussion = Discussion.objects.get(pk=discussion_id)

    if 'title' not in request.POST:
        context = {
            'title': discussion.title,
            'description': discussion.description,
        }
        form = loader.get_template('whisper/update_discussion.html').render(context, request)
        return HttpResponse(form)

    title = request.POST['title']
    if len(title) > 128:
        title = title[:128]
        pass
    description = request.POST['description']
    if len(description) > settings.DISCUSSION_MAX_LENGTH:
        description = description[:512]
        pass

    user = discussion.user
    user_id = int(request.session['_auth_user_id'])
    if user.id != user_id:
        raise 'Invalid user ID'

    if title == discussion.title and description == discussion.description:
        return redirect('/whisper/discuss/' + str(discussion.id) + '/p/')

    dhist = DiscussionHistory(discussion=discussion,
                              title=discussion.title,
                              description=discussion.description,
                              publish_time=discussion.publish_time)
    dhist.save()

    discussion.title = title
    discussion.description = description
    discussion.publish_time = datetime.now()
    discussion.save()

    return redirect('/whisper/discuss/' + str(discussion.id) + '/p/')

def show_user_discussions(request, user_name):
    user = User.objects.get(username=user_name)
    discussions = \
        Discussion.objects.filter(user=user).order_by('publish_time').reverse()[:25]
    discussions = [
        {
            'id': discuss.id,
            'title': discuss.title,
            'description': discuss.description,
        }
        for discuss in discussions]
    context = {
        'user_name': user.username,
        'discussions': discussions
        }
    discussion_list = \
        loader.get_template('whisper/user_discussions.html').render(context)

    return render_view(request, '', 'whisper/code', 'whiper/comment',
                       'whisper/new_discussion',
                       0, [], '', discussion_list, '')

def user_functions(request, path):
    parts = path.split('/')
    user = parts[1]
    func = parts[2]
    if func == 'discussions':
        return show_user_discussions(request, user)
    return redirect('/whisper/code')

@ensure_csrf_cookie
def index(request, **kws):
    try:
        path = kws['path']
    except:
        path = ''
        pass
    path = path.strip('/')

    path_parts = path.split('/')
    func = path_parts[0]
    comments = []
    discussion_id = 0
    if func == 'code':
        site_rel_root = 'whisper/code'
        if len(path_parts) == 1:
            path = ''
        else:
            path = os.path.join(*path_parts[1:])
            pass
    elif func == 'discuss':
        discussion_id = int(path_parts[1])
        comments = get_comments(discussion_id)
        if comments is None:
            return

        site_rel_root = os.path.join('whisper', func, str(discussion_id), 'p')
        if len(path_parts) == 3:
            path = ''
        else:
            path = os.path.join(*path_parts[3:])
            pass
    elif func == 'comment':
        if '_auth_user_id' not in request.session:
            return redirect('/accounts/login')
        return add_comment(request, path)
    elif func == 'update_comment':
        if '_auth_user_id' not in request.session:
            return redirect('/accounts/login')
        return update_comment(request, path)
    elif func == 'new_discussion':
        if '_auth_user_id' not in request.session:
            return redirect('/accounts/login')
        return new_discussion(request)
    elif func == 'create_discussion':
        if '_auth_user_id' not in request.session:
            return redirect('/accounts/login')
        return create_discussion(request)
    elif func == 'update_discussion':
        if '_auth_user_id' not in request.session:
            return redirect('/accounts/login')
        return update_discussion(request, path)
    elif func == 'user':
        return user_functions(request, path)
    else:
        return redirect('/whisper/code')

    site_cmtpath = 'whisper/comment'
    site_newdiscusspath = 'whisper/new_discussion'
    return show_view(request, path, site_rel_root, site_cmtpath,
                     site_newdiscusspath,
                     discussion_id, comments)

