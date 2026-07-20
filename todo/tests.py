from django.test import TestCase, Client
from django.utils import timezone
from datetime import datetime
from todo.models import Task


class SampleTestCase(TestCase):
    def test_sample1(self):
        self.assertEqual(1 + 2, 3)


class TaskModelTestCase(TestCase):
    def test_create_task1(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        task = Task(title='task1', due_at=due)
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task1')
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, due)

    def test_create_task2(self):
        task = Task(title='task2')
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task2')
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, None)

    def test_create_task_with_priority(self):
        task = Task(title='task3', priority=True)
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertTrue(task.priority)

    def test_is_overdue_future(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 6, 30, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()

        self.assertFalse(task.is_overdue(current))

    def test_is_overdue_past(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()

        self.assertTrue(task.is_overdue(current))

    def test_is_overdue_none(self):
        due = None
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()

        self.assertFalse(task.is_overdue(current))


class TodoViewTestCase(TestCase):
    def test_index_get(self):
        client = Client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context['tasks']), 0)

    def test_index_post(self):
        client = Client()
        data = {'title': 'Test Task', 'due_at': '2024-06-30 23:59:59'}
        response = client.post('/', data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context['tasks']), 1)

    def test_index_post_with_priority(self):
        client = Client()
        data = {'title': 'Prioritized Task', 'due_at': '2024-06-30 23:59:59', 'priority': 'true'}
        response = client.post('/', data)
        self.assertEqual(response.status_code, 200)
        task = Task.objects.get(title='Prioritized Task')
        self.assertTrue(task.priority)

    def test_index_get_order_post(self):
        task1 = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title='task2', due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()

        client = Client()
        response = client.get('/?order=post')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(response.context['tasks'][0], task2)
        self.assertEqual(response.context['tasks'][1], task1)

    def test_index_get_order_due(self):
        task1 = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title='task2', due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()

        client = Client()
        response = client.get('/?order=due')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(response.context['tasks'][0], task1)
        self.assertEqual(response.context['tasks'][1], task2)

    def test_index_get_order_priority(self):
        task1 = Task(title='task1', priority=True)
        task1.save()
        task2 = Task(title='task2', priority=False)
        task2.save()
        task3 = Task(title='task3')
        task3.save()

        client = Client()
        response = client.get('/?order=priority')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(response.context['tasks'][0], task1)

    def test_update_get_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get('/{}/update'.format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/edit.html')
        self.assertEqual(response.context['task'], task)

    def test_update_post_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.post(
            '/{}/update'.format(task.pk),
            {'title': 'updated task', 'due_at': '2024-08-01T12:30:00'}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/{}/'.format(task.pk))

        task.refresh_from_db()
        self.assertEqual(task.title, 'updated task')
        self.assertEqual(task.due_at, timezone.make_aware(datetime(2024, 8, 1, 12, 30, 0)))

    def test_detail_get_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get('/{}/'.format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/detail.html')
        self.assertEqual(response.context['task'], task)

    def test_delete_get_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get('/{}/delete'.format(task.pk))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/')
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_detail_get_fail(self):
        client = Client()
        response = client.get('/1/')
        self.assertEqual(response.status_code, 404)

    def test_delete_get_fail(self):
        client = Client()
        response = client.get('/1/delete')
        self.assertEqual(response.status_code, 404)

    def test_close_marks_task_completed_and_shows_completion_message(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()

        response = client.get('/{}/close'.format(task.pk), follow=True)

        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertTrue(task.completed)
        self.assertContains(response, '達成')
        self.assertContains(response, '達成率')

    def test_index_includes_completion_stats(self):
        Task.objects.create(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)), completed=True)
        Task.objects.create(title='task2', due_at=timezone.make_aware(datetime(2024, 8, 1)))

        client = Client()
        response = client.get('/')

        self.assertEqual(response.context['total_tasks'], 2)
        self.assertEqual(response.context['completed_count'], 1)
        self.assertEqual(response.context['completion_rate'], 50)

    def test_delete_task_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()

        response = client.post('/task/{}/delete/'.format(task.pk))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.filter(pk=task.pk).count(), 0)

    def test_delete_task_not_found(self):
        client = Client()
        response = client.post('/task/999/delete/')
        self.assertEqual(response.status_code, 404)
