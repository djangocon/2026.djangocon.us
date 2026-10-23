---
category: talks
end_datetime: 2026-08-24 16:35:00-05:00
permalink: /talks/teach-django-tasks-to-speak-celery-building-a-celery-backend-for-django-tasks/
presenter_slugs:
- matias-bordese
room: Sauganash Ballroom
start_datetime: 2026-08-24 16:10:00-05:00
tags:
- Architecture
- IPC
- Celery
- Tasks
title: 'Teach Django Tasks to speak Celery: Building a Celery backend for Django Tasks'
track: t0
---

Django 6.0 introduced Django Tasks, a built-in framework for defining and queuing background jobs to run code outside the HTTP request–response cycle. Django ships by default with backends for development and testing, but production systems often rely on distributed task queues like Celery. How do we bridge that gap?
In this talk, I'll show how Django Tasks works under the hood, and walk through a Celery backend implementation that lets you run Django tasks on Celery workers without changing your application code.

What this talk will be about:

- What Django Tasks is and how it works: the new standard API for background jobs in Django 6.0.
- How task backends act as adapters between task APIs and execution engines.
- How a Celery backend translates Django tasks into Celery jobs.
- A practical demo highlighting the pluggable architecture (switch your backend to use Celery without changing code!).

No prior experience with Celery is needed.
