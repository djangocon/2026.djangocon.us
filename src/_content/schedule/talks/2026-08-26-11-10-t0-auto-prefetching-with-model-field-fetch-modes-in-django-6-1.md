---
category: talks
end_datetime: 2026-08-26 11:35:00-05:00
permalink: /talks/auto-prefetching-with-model-field-fetch-modes-in-django-6-1/
presenter_slugs:
- jacob-walls
room: Sauganash Ballroom
start_datetime: 2026-08-26 11:10:00-05:00
tags:
- Improvements
- internals
- Deep dive
title: Auto-prefetching with model field fetch modes in Django 6.1
track: t0
---

New in Django 6.1, model field fetch modes provide a way to avoid the deluge of queries from accessing un-fetched objects during a loop (also known as the "N+1 queries" problem). You may be familiar with how Django's prefetch_related() and select_related() methods can prevent these queries, but unlike those tools, the "fetch peers" mode does not require maintaining a list of fields to fetch. This can significantly improve project maintenance, especially when QuerySets are constructed at some distance from where they are used.

In this talk, we'll cover what's new about fetch modes, what tradeoffs are entailed, how to configure fetch modes per-model via managers, and how to use the "raise" mode to surface issues in development or put guardrails around performance-intensive sections of code.