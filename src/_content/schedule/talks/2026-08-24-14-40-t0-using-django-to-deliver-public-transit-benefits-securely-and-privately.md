---
category: talks
end_datetime: 2026-08-24 15:05:00-05:00
permalink: /talks/using-django-to-deliver-public-transit-benefits-securely-and-privately/
presenter_slugs:
- scott-cranfill
room: Sauganash Ballroom
start_datetime: 2026-08-24 14:40:00-05:00
tags:
- use case
- Security
title: Using Django to deliver public transit benefits securely and privately
track: t0
---

[Cal-ITP Benefits](https://benefits.calitp.org) is an [open-source Django application](https://github.com/cal-itp/benefits) funded by the state of California as part of the [California Integrated Travel Project](https://www.calitp.org). It provides a way for riders to confirm their eligibility for public transit benefits and then register their credit or debit card so they automatically receive reduced fares when they tap to pay. This product aims to make open-loop payments accessible to all transit riders, while providing a convenient digital enrollment path for reduced fares that limits the need for in-person trips to a transit center.

In this talk we will discuss how Cal-ITP Benefits is architected with a focus on user privacy. The app utilizes the [California Identity Gateway](https://cdt.ca.gov/digitalid/) to digitally verify a rider’s identity and confirm their eligibility for transit benefits using a variety of state and federal government partners, including [Login.gov](https://login.gov), [Medicare.gov](https://www.medicare.gov), the [Veterans Administration](https://www.va.gov), and the [California Department of Social Services](https://cdss.ca.gov). All personally identifiable information (PII) is managed external to the application; our app has no end-user accounts and only a small database for configuration.

Join us to learn how our solution…

- Leverages core Django features to provide the self-service front end and the Django Admin back end that supports both transit provider staff doing in-person enrollments and Cal-ITP staff managing configuration
- Prioritizes user privacy and helps transit providers administer a lightweight, compliant fare discount program that eliminates the need to store and manage sensitive rider data
- Uses existing data sources rather than rider input to confirm a person’s eligibility for transit benefits
- Creates a modular, reproducible digital identification and eligibility confirmation model that is available for reuse by other states or the federal government