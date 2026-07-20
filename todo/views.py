from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from todo.models import Task
from django.db.models import F
# Create your views here.


def _get_rating_from_session(request, task_id):
    return request.session.get(f'task_rating_{task_id}', None)


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

    for task in tasks:
        setattr(task, 'rating_value', request.session.get(f'task_rating_{task.id}', None))

    context = {
        'tasks': tasks,
    }
    return render(request, 'todo/index.html', context)


def detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    show_close_form = request.GET.get('show_close_form') == '1'
    rating_value = _get_rating_from_session(request, task_id)
    if rating_value is None:
        rating_value = task.rating
    context = {
        'task': task,
        'show_close_form': show_close_form,
        'ratings': range(1, 6),
        'rating_value': rating_value,
    }
    return render(request, 'todo/detail.html', context)


def close(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    if request.method == 'POST':
        rating_value = request.POST.get('rating', '0')
        try:
            task.rating = int(rating_value)
        except ValueError:
            task.rating = 0
        request.session[f'task_rating_{task_id}'] = str(task.rating)
        task.completed = True
        task.save()
        return redirect(index)

    return redirect('detail', task_id=task_id)

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
