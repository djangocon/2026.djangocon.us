---
category: talks
end_datetime: 2026-08-25 17:25:00-05:00
permalink: /talks/keeping-pace-with-django-evolving-through-15-years-of-updates/
presenter_slugs:
- eduardo-felipe-castegnaro
room: Sauganash Ballroom
start_datetime: 2026-08-25 17:00:00-05:00
tags:
- use case
- Maintenance
title: 'Keeping Pace with Django: Evolving Through 15 years of Updates'
track: t0
---

Working on the same codebase for 15 years is not something that you plan on doing. It's something that happens organically. As the years go on and the business requirements become ever more complex, you'll need to keep up with the stack to be able to deliver the product your users expect.

This talk will cover what worked (and what didn't) while building and running a codebase in production for over 15 years. You'll find out what it takes to bring a project from Python 2.6 and Django 1.2 all the way to Python 3.14 and Django 5.2.

We’ll explore how following release cycles, understanding release notes and deprecation policies helps you write code that is low maintenance while flexible enough to change when the time comes.

There will be samples of how individual views in the project were updated to take advantage of new features in the framework, including dropping dependencies when third-party libraries eventually made their way into Django.

Sometimes there might be a need to create workarounds for breaking changes or even backport a patch, so we'll also go over some tips on when bending the rules is the right decision.
