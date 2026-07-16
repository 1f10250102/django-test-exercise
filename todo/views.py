from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from todo.models import Task
# Create your views here.


def index(request):
    if request.method == 'POST':
        due_at_raw = request.POST.get('due_at')
        due_at = make_aware(parse_datetime(due_at_raw)) if due_at_raw else None
        priority_raw = request.POST.get('priority')
        priority = priority_raw == 'true'
        task = Task(title=request.POST['title'],
                    due_at=due_at,
                    priority=priority)
        task.save()

    if request.GET.get('order') == 'due':
        tasks = Task.objects.order_by('due_at')
    elif request.GET.get('order') == 'priority':
        tasks = sorted(
            Task.objects.all(),
            key=lambda task: (not task.priority, task.posted_at)
        )
    else:
        tasks = Task.objects.order_by('-posted_at')

    context = {
        'tasks': tasks
    }
    return render(request, 'todo/index.html', context)


def detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    context = {
        'task': task,
    }
    return render(request, 'todo/detail.html', context)


def close(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    task.completed = True
    task.save()
    return redirect(index)

def delete(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404('Task does not exist')
    task.delete()
    return redirect(index)

def update(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404('Task does not exist')
    if request.method == 'POST':
        task.title = request.POST['title']
        due_at_raw = request.POST.get('due_at')
        task.due_at = make_aware(parse_datetime(due_at_raw)) if due_at_raw else None
        priority_raw = request.POST.get('priority')
        task.priority = priority_raw == 'true'
        task.save()
        return redirect(detail, task_id)
    
    context = {
        'task': task
    }
    return render(request, 'todo/edit.html', context)


def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.delete()
    return redirect('index')
