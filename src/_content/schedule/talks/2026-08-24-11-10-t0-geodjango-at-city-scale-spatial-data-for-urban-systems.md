---
category: talks
end_datetime: 2026-08-24 11:35:00-05:00
permalink: /talks/geodjango-at-city-scale-spatial-data-for-urban-systems/
presenter_slugs:
- drishti-jain
room: Sauganash Ballroom
start_datetime: 2026-08-24 11:10:00-05:00
tags:
- GeoDjango
title: 'GeoDjango at City Scale: Spatial Data for Urban Systems'
track: t0
---

In this talk, I’ll delve into how GeoDjango can be used to build scalable spatial data platforms for smart cities and urban systems. Cities are fundamentally spatial systems—roads, buildings, utilities, mobility flows, and environmental sensors all exist in geographic space—and modeling these systems requires tools that can handle geospatial data at scale. GeoDjango, combined with PostGIS, provides a powerful framework for representing, querying, and visualizing this spatial information in web applications.
I’ll begin by exploring how urban entities such as buildings, transit routes, sensor locations, and zoning boundaries can be modeled using GeoDjango’s spatial fields and ORM abstractions. Attendees will see how spatial indexes and geospatial queries enable proximity search, containment checks, routing queries, and large-scale spatial analytics directly from Django applications.
Next, I’ll examine architectural and performance considerations for city-scale spatial systems, including indexing strategies, partitioning spatial datasets, and optimizing geospatial queries for low latency. We’ll discuss how GeoDjango fits into modern data pipelines, integrating with streaming telemetry, GIS data sources, and visualization layers such as interactive maps and dashboards.
Finally, I’ll discuss how spatial data platforms inform urban planning, infrastructure management, and policy decisions, and how Django-based systems can serve as the backbone for civic analytics and public data platforms. Throughout the talk, attendees will gain practical and conceptual tools for building geospatially-aware web systems and a deeper understanding of how Django can power the spatial intelligence layer of modern cities.