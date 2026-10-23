---
category: talks
end_datetime: 2026-08-26 11:05:00-05:00
permalink: /talks/scaling-django-mastering-database-routers-with-aws-aurora/
presenter_slugs:
- leonardo-batista
room: Sauganash Ballroom
start_datetime: 2026-08-26 10:20:00-05:00
tags:
- Cloud
- scaling
- use case
- ORM
- internals
- deployment
title: 'Scaling Django: Mastering Database Routers with AWS Aurora'
track: t0
---

As your Django application grows, the database is often the first major bottleneck. But how do you scale horizontally without introducing massive complexity into your application logic? In this talk, we’ll explore how OneBlinc leveraged Django's native Database Routers to distribute load across an AWS Aurora cluster. We will go beyond the documentation to discuss real-world implementation: managing read/write splitting, handling replication lag, ensuring data consistency in financial transactions. If you want to squeeze every bit of performance out of your cloud database while keeping your Django code clean, this session is for you.