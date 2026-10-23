---
category: talks
end_datetime: 2026-08-26 16:05:00-05:00
permalink: /talks/the-django-uuid-story/
presenter_slugs:
- paolo-melchiorre
room: Sauganash Ballroom
start_datetime: 2026-08-26 15:40:00-05:00
tags:
- Databases
title: The Django UUID Story
track: t0
---

My first larger contribution to **Django** started during the sprints at *DjangoCon Europe 2017* in *Florence*, where I worked on exposing database-side **RandomUUID** generation for UUIDv4 in `contrib.postgres`, so for me this topic has a very personal history inside the project.

Since then the way Django handles **UUID** generation has evolved, and recent changes extended these functions beyond PostgreSQL while also adding support for **UUIDv7**, which brings time ordering and new possibilities for modern database schemas.

In this talk I show how these UUID functions work in Django today, how **UUIDv4** and **UUIDv7** differ in practice, and how Django can generate UUID values at the Python side or at the **database** side depending on the backend and the use case.

This talk is especially useful for developers who already know Django models and want to better understand how **UUID** generation fits into real applications, migrations and schema design, especially now that support is broader and more flexible than before.
