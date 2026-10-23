---
category: talks
end_datetime: 2026-08-26 14:35:00-05:00
permalink: /talks/wishlist-granted-htmx-without-betraying-your-django-views/
presenter_slugs:
- natalia
room: Sauganash Ballroom
start_datetime: 2026-08-26 13:50:00-05:00
tags:
- HTMX
- UI/UX
- flexible time
- Deep dive
title: 'Wishlist granted: HTMX without betraying your Django views'
track: t0
---

A feature built the traditional Django way. Making it dynamic is next. What do you do? The answer is simpler than you think!

Starting from a plain server-rendered implementation, my goal was to avoid full-page reloads without throwing away what I had already built, and without reaching for a new tool or a new architecture. Template partials and HTMX turned out to be exactly the right fit. The changes were small and targeted, the code stayed readable, and I never had to leave my Django safe place.

This talk is about a real project, real decisions, and what progressive enhancement in Django can look like in practice using modern tools, one small change at a time.
