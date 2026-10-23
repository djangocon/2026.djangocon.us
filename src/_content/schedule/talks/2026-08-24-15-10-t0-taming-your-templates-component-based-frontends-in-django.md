---
category: talks
end_datetime: 2026-08-24 15:35:00-05:00
permalink: /talks/taming-your-templates-component-based-frontends-in-django/
presenter_slugs:
- kasey-kelly
room: Sauganash Ballroom
start_datetime: 2026-08-24 15:10:00-05:00
tags:
- Templates
- Architecture
- flexible time
title: 'Taming Your Templates: Component-Based Frontends in Django'
track: t0
---

Most Django teams treat their templates as second-class citizens.

Logic gets carefully organized into models, views, and services, then dumped into a `{&#37; include %}` chain that nobody fully understands six months later. Context variables appear from nowhere, component boundaries exist only in the original author's memory, and the onboarding docs are "just ask someone."

This talk argues that your templates deserve the same respect as the rest of your stack and shows you how to get there without abandoning Django's template system or adding a heavy JavaScript build pipeline.

We'll cover the component mental model in plain Django, an honest assessment of your tooling options (built-in includes, django-includecontents, django-cotton, and more), and how to know when a plain `{&#37; include %}` is still the right answer. We'll close with pattern libraries and how explicit component contracts make AI-assisted development dramatically more reliable.

Attendees leave with a concrete sense of best practices they can apply to a new project or use to incrementally improve an existing one. No headless architecture required.
