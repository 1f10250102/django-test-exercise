from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from todo.models import Task
from django.db.models import F
# Create your views here.


def index(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        due_value = request.POST.get('due_at')
        task_data = {'title': title}
        if due_value:
            task_data['due_at'] = make_aware(parse_datetime(due_value))

        priority_raw = request.POST.get('priority')
        task_data['priority'] = priority_raw == 'true'
        task = Task(**task_data)
        task.save()

    # Default: order by due date (nulls last)
    order = request.GET.get('order')
    if order == 'due':
        tasks = Task.objects.order_by(F('due_at').asc(nulls_last=True))
    elif order == 'priority':
        # Group by priority (high first) and within each group sort by due date
        tasks = Task.objects.order_by(F('priority').desc(), F('due_at').asc(nulls_last=True))
    elif order == 'post':
        tasks = Task.objects.order_by('-posted_at')
    else:
        tasks = Task.objects.order_by(F('due_at').asc(nulls_last=True))

    total_tasks = Task.objects.count()
    completed_count = Task.objects.filter(completed=True).count()
    completion_rate = int(completed_count / total_tasks * 100) if total_tasks else 0

    context = {
        'tasks': tasks,
        'total_tasks': total_tasks,
        'completed_count': completed_count,
        'completion_rate': completion_rate,
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
    messages.success(request, '達成！おめでとうございます。')
    return redirect('index')


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
