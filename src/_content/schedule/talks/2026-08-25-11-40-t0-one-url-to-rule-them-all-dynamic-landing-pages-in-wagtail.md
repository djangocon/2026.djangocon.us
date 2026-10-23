---
category: talks
end_datetime: 2026-08-25 12:05:00-05:00
permalink: /talks/one-url-to-rule-them-all-dynamic-landing-pages-in-wagtail/
presenter_slugs:
- chrissy-wainwright
room: Sauganash Ballroom
start_datetime: 2026-08-25 11:40:00-05:00
tags:
- Wagtail
title: 'One URL to Rule Them All: Dynamic Landing Pages in Wagtail'
track: t0
---

Every marketing campaign has the same problem: one message, a dozen audiences, and suddenly your CMS is drowning in nearly identical pages. For Truth Initiative, the nation’s largest nonprofit dedicated to ending nicotine addiction, editors were maintaining a growing library of duplicate landing pages with no clean way to test what was actually working.

We solved it with a dynamic Wagtail landing page, built on a Django backend, that tracks users based on the last URL segment (e.g., /youtube, /facebook). A/B testing was baked in at the CMS level to help test different features against a percentage of the audience. Editors now manage a single page design for tailoring text, CTAs, and creative assets.

This session covers:

- The business problem of campaign duplication.
- How we used Django and Wagtail to manage user tracking using a single landing page
- How A/B testing was implemented for testing different text within the page
- The impact: reduced editor workload, faster rollouts, and consistent design across channels.

Attendees will walk away with a scalable, editor-friendly model for tackling personalization without drowning in duplicate content.