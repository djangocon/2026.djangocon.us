---
category: talks
end_datetime: 2026-08-24 14:35:00-05:00
permalink: /talks/search-as-you-type-for-54-million-names-postgresql-django-for-fuzzy-name-matching-at-scale/
presenter_slugs:
- tobias-mcnulty
- gerald-carlton
room: Sauganash Ballroom
start_datetime: 2026-08-24 13:50:00-05:00
tags:
- use case
- postgres
title: 'Search-as-you-type for 54 Million Names: PostgreSQL + Django for Fuzzy Name
  Matching at Scale'
track: t0
---

Searching for human names in large datasets is harder than it looks. A user searches for "Smith, John," but the database contains "Smyth, Jon" or "Smithe, Johnny." Standard `LIKE` queries are too strict, full-text search doesn't handle name nuances well, and unindexed fuzzy matching won't scale.

This talk covers how we solved these problems for RecordsDB, a Django app that searches over 50 million North Carolina court records for legal aid organizations and public defenders.

## Talk Structure

The session is structured as a technical walkthrough using a Jupyter notebook and a sample Django app. I’ll demonstrate the pitfalls of name searching and how to implement performant solutions. The notebook and source code will be available at the start of the talk so you can follow along.

We’ll cover how to use PostgreSQL phonetic algorithms (Soundex, Daitch-Mokotoff), fuzzy string matching (Levenshtein), and specific indexing strategies to keep searches fast across 50M+ records.

### Problem Space
* **The Challenges:** Why name search fails (spelling variations, typos, nicknames).
* **Scale:** Why techniques that work for 10k records break at 1M+.
* **Case Study:** Lessons from a 54-million-record production database.

### PostgreSQL Techniques
* **Phonetic Matching:** Using Daitch-Mokotoff to find similar-sounding names with different spellings.
* **Fuzzy Matching:** Using Levenshtein distance for typo tolerance.
* **Indexing for Performance:**
    * GIN indexes for phonetic matching.
    * B-tree with `text_pattern_ops` for prefix searches.
    * Performance gains from `COLLATE "C"`.
    * Trade-offs between index size and query speed.

### Django Implementation
* **ORM Integration:** Writing custom QuerySet methods and wrapping Postgres functions with `RawSQL` or custom `Func` expressions.
* **Custom Indexes:** Defining specific Postgres indexes in Django models.
* **Fast Type-ahead:** Building search-as-you-type interfaces that stay responsive at scale.
* **Benchmarks:** Comparing query times across different search strategies.

### Lessons Learned
* **UX:** When to use fuzzy matching versus when it creates too much noise.
* **Maintenance:** Managing large indexes in production.
* **Accuracy:** Balancing precision and recall in legal and public service contexts.
