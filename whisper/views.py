from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import ensure_csrf_cookie
from .srcsvc import SourceService

from .models import File, Discussion, Comment
from django.contrib.auth.models import User

import os
import itertools

from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.formatters import HtmlFormatter

from datetime import datetime

srcs = SourceService()

def get_comments(discussion_id):
    discussion = Discussion.objects.get(id=discussion_id)
    if not discussion:
        return None

    comments = [{'path': cmt.filename.path,
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
                    'description': dis.description}
                   for dis in discussions]
    context = {'discussions': discussions}
    template = loader.get_template('whisper/empty.html');
    source = template.render(context, request)
    return source

def show_view(request, path, site_relpath, site_cmtpath,
              site_newdiscusspath,
              discussion_id, comments):
    if srcs.is_file(path):
        origin = path
        filename = os.path.basename(path)
        path = os.path.dirname(path).strip('/')
        try:
            lexer = get_lexer_for_filename(filename)
            formatter = HtmlFormatter(linenos=True,
                                      cssclass="source",
                                      full=True,
                                      linespans='line',
                                      title=filename)
            code = open(srcs.abs(origin)).read()
            source = highlight(code, lexer, formatter)
        except:
            source = empty(request)
            pass
    else:
        filename = ''
        source = empty(request)
        pass

    if '_auth_user_id' in request.session:
        user = User.objects.get(pk=request.session['_auth_user_id'])
        username = user.username
    else:
        username = ''
        pass

    if discussion_id:
        dis = Discussion.objects.get(pk=discussion_id)
        discussion_title = dis.title
        discussion_description = dis.description
        pass

    dirs, files, relpath = srcs.list(path)
    dirs.sort()
    files.sort()
    template = loader.get_template('whisper/codeview.html')
    context = {
        'comments': comments,
        'subdirectories': dirs,
        'files': files,
        'user': username,
        'source': source,
        'relpath': relpath,
        'filename': filename,
        'site_relpath': site_relpath,
        'site_cmtpath': site_cmtpath,
        'site_newdiscusspath': site_newdiscusspath,
        'discussion_id': discussion_id,
    }
    if discussion_id:
        dis = Discussion.objects.get(pk=discussion_id)
        context['discussion_title'] = dis.title
        context['discussion_description'] = dis.description
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

    user = User.objects.get(id=1)
    cmt = Comment(discussion=dis,
                  reply_to=reply_to,
                  user=user,
                  filename=fo,
                  lineno=line_no,
                  content=content,
                  publish_time=datetime.now())
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
        description = description[512]
        pass
    discussion = Discussion(title=title, description=description,
                            publish_time=datetime.now())
    discussion.save()
    return redirect('/whisper/discuss/' + str(discussion.id) + '/p/')

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
        site_relpath = 'whisper/code'
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

        site_relpath = os.path.join('whisper', func, str(discussion_id), 'p')
        if len(path_parts) == 3:
            path = ''
        else:
            path = os.path.join(*path_parts[3:])
            pass
    elif func == 'comment':
        if '_auth_user_id' not in request.session:
            return redirect('/accounts/login')
        return add_comment(request, path)
    elif func == 'new_discussion':
        if '_auth_user_id' not in request.session:
            return redirect('/accounts/login')
        return new_discussion(request)
    elif func == 'create_discussion':
        if '_auth_user_id' not in request.session:
            return redirect('/accounts/login')
        return create_discussion(request)
    else:
        return redirect('/whisper/code')

    site_cmtpath = 'whisper/comment'
    site_newdiscusspath = 'whisper/new_discussion'
    return show_view(request, path, site_relpath, site_cmtpath,
                     site_newdiscusspath,
                     discussion_id, comments)

