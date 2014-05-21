import re
import requests

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.views.generic import View

from stucampus.minivideo.models import Resource
from stucampus.minivideo.forms import SignUpForm, CommitForm, loginForm
from stucampus.account.permission import check_perms


class SignUpView(View):
    def get(self, request):
        resource_id = request.GET.get('id')
        if resource_id is None:
            form = SignUpForm()
            flag = False
            return render(request, 'minivideo/signup.html', {'form':form,'flag':flag})

        flag = True
        resource = get_object_or_404(Resource, pk=resource_id)

        perm = True
        if not request.user.has_perm('minivideo.manager'):
            if not 'stuno' in request.session:
                return HttpResponseRedirect( reverse('minivideo:login') )
            else:
                if request.session['stuno'] != resource.team_captain_stuno:
                    perm = False

        form = CommitForm(instance=resource)

        url = 'http://v.youku.com/v_show/id_(.*?).html'
        req = re.compile(url)
        number = re.search(req, resource.video_link)
        if number:
            number = number.group(1)
            
        return render(request, 'minivideo/signup.html', {'form':form,'flag':flag,'resource':resource,'number':number,'personal_perm':perm})

    def post(self, request):
        resource_id = request.GET.get('id')
        if resource_id is None:
            form = SignUpForm(request.POST)
            flag = False
            if not form.is_valid():
                return render(request, 'minivideo/signup.html', {'form':form,'flag':flag})
            form.save()
            return HttpResponseRedirect(reverse('minivideo:resource_list'))
        flag = True
        resource = Resource.objects.get(team_captain_stuno=request.POST['team_captain_stuno'])
        form = CommitForm(request.POST,request.FILES,instance=resource)
        if not form.is_valid():
            return render(request, 'minivideo/signup.html', {'form':form,'flag':flag})
        resource.has_verified = False
        form.save()
        return HttpResponseRedirect( reverse('minivideo:details')+'?id='+str(resource.id) )


def resource_list(request):
    resources = Resource.objects.all().order_by('has_verified','id')
    page = request.GET.get('page')
    paginator = Paginator(resources,15)
    try:
        page_list = paginator.page(page)
    except PageNotAnInteger:
        page_list = paginator.page(1)
    except EmptyPage:
        page_list = paginator.page(paginator.num_pages)

    return render(request,'minivideo/list.html',{ 'page_list':page_list})


@check_perms('minivideo.manager')
def verify(request):
    resource_id = request.GET.get('id')
    resource = get_object_or_404(Resource,pk=resource_id)
    resource.has_verified = not resource.has_verified
    resource.save()
    return HttpResponseRedirect(reverse('minivideo:resource_list'))


def index(request):
    resources = Resource.objects.all().filter(has_verified=True).order_by('?')
    return render(request,'minivideo/index.html',{'resources':resources})


def details(request):
    resource_id = request.GET.get('id')
    resource = get_object_or_404(Resource,pk=resource_id)
    perm = True
    if not request.user.has_perm('minivideo.manager'):
        if not 'stuno' in request.session:
            return HttpResponseRedirect( reverse('minivideo:login') )
        else:
            if request.session['stuno'] != resource.team_captain_stuno:
                perm = False

    url = 'http://v.youku.com/v_show/id_(.*?).html'
    req = re.compile(url)
    number = re.search(req, resource.video_link)
    if number:
        number = number.group(1)
    return render(request,'minivideo/details.html',{'resource':resource, 'number' : number,'personal_perm':perm})


@check_perms('minivideo.manager')
def resource_delete(request):
    resource_id = request.GET.get('id')
    resource = get_object_or_404(Resource,pk=resource_id)
    resource.delete()
    return HttpResponseRedirect(reverse('minivideo:resource_list'))


class LoginView(View):
    
    def get(self, request):
        if 'stuno' in request.session:
            return HttpResponseRedirect(reverse('minivideo:resource_list'))
        form = loginForm()
        return render(request,'minivideo/login.html',{'form':form})

    def post(self, request):
        form = loginForm(request.POST)
        if not form.is_valid():
            return render(request, 'minivideo/login.html', {'form':form})
        request.session['stuno'] = request.POST['team_captain_stuno']
        request.session.set_expiry(0)
        return HttpResponseRedirect(reverse('minivideo:resource_list'))