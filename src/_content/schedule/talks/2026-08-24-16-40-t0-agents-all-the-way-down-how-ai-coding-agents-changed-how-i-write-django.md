---
category: talks
end_datetime: 2026-08-24 17:05:00-05:00
permalink: /talks/agents-all-the-way-down-how-ai-coding-agents-changed-how-i-write-django/
presenter_slugs:
- josh-thomas
room: Sauganash Ballroom
start_datetime: 2026-08-24 16:40:00-05:00
tags:
- use case
- Architecture
- Using AI in development
title: 'Agents All the Way Down: How AI Coding Agents Changed How I Write Django'
track: t0
---

I'm the lead developer at a company with about 10 Django applications. The biggest is a 19-year-old legacy application that's been ported from ColdFusion to WordPress to a custom PHP system to Django. It's full of boolean fields that should be foreign keys, invariants that live in developers' heads instead of model constraints, and business logic that predates Django's existence. I've been using coding agents on this codebase and others for the past year, mostly Claude Code.

The most interesting result isn't speed. What actually changed is how I write Django. I lean harder into the ORM, encoding invariants in model relationships instead of application logic, because agents are good at following the framework's conventions and bad at following mine. I build less custom scaffolding, and when I do, I build it out of wood instead of concrete, designed to be torn down as the tools improve. I got my test suite runtime as low as possible, because a fast feedback loop is the difference between an agent that can verify its own work and one that's guessing.

Most advice about coding agents is "here's how to prompt better." This talk is about how working with agents changes the way you structure a Django project. I'll cover where agents help with legacy code, where they fall down specifically with Django (migrations, multi-app relationships, project conventions), and the feedback loop: you reshape the codebase for agents, and that reshaping makes the code better for humans too.

This talk is for Django developers who are past the "wow, it wrote a function" phase.
