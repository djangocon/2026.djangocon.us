---
category: talks
end_datetime: 2026-08-25 15:05:00-05:00
permalink: /talks/polyglot-persistence-with-django-when-one-database-isn-t-enough/
presenter_slugs:
- abigail-afi-gbadago
room: Sauganash Ballroom
start_datetime: 2026-08-25 14:40:00-05:00
tags:
- Databases
- Architecture
- non-relational DB
title: 'Polyglot Persistence with Django: When One Database Isn''t Enough'
track: t0
---

Polyglot persistence is the use of multiple databases in a single application, with each chosen for what it does best. Django ships with multi-database support: define your connections, write a router, and in theory, you're done. In practice, the gap between "Django supports this" and "I have this working" is where most developers get stuck. This talk closes that gap by using a Django MongoDB backend alongside PostgreSQL, with honest coverage of where the ORM abstraction leaks, what migrations look like against a document store, and lessons learned from building with MongoDB's Queryable Encryption in a real Django context. Attendees leave with working patterns, a clear decision framework, and an answer to whether polyglot persistence is the best choice for their project.
