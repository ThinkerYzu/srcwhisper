from django.conf import settings
from django import forms
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from hashlib import sha256
import tempfile
import os

class UploadFileForm(forms.Form):
    file = forms.FileField()
    pass

def save_uploaded_file(uploaded_file):
    fo = tempfile.NamedTemporaryFile(dir=settings.USER_CODE_REPO,
                                     delete=False)
    tmpname = fo.name
    m = sha256()
    fname = os.path.basename(uploaded_file.name)
    fo.write(bytes(fname + '\n', 'utf-8'))
    m.update(bytes(fname + '\n', 'utf-8'))
    for chunk in uploaded_file.chunks():
        fo.write(chunk)
        m.update(chunk)
        pass
    fo.close()

    hashcode = m.hexdigest()
    os.rename(tmpname, os.path.join(settings.USER_CODE_REPO, hashcode))

    return hashcode

@ensure_csrf_cookie
def upload_file(request, discussion_id=0):
    if '_auth_user_id' not in request.session:
        return redirect('/accounts/login')

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['file']
            if f.size <= 100 * 1024:
                hashcode = save_uploaded_file(request.FILES['file'])
                if discussion_id:
                    return redirect('/whisper/discuss/' + str(discussion_id) + '/p/:ucode:/' + hashcode)
                else:
                    return redirect('/whisper/code/:ucode:/' + hashcode)
            pass
        pass

    form = UploadFileForm()
    return render(request, 'whisper/user_code_upload.html',
                  {'form': form})
