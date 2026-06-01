---
layout: archive
title: "Publications"
permalink: /publications/
author_profile: true
---

{% if author.googlescholar %}
  You can also find my full publication list on <u><a href="{{author.googlescholar}}">my Google Scholar profile</a>.</u>
{% endif %}

{% include base_path %}

{% assign highlighted_pubs = site.data.featured_publications | sort: "citations" | reverse | slice: 0, 5 %}
{% assign highlighted_pubs = highlighted_pubs | sort: "year" | reverse %}
{% assign current_year = "" %}
{% for pub in highlighted_pubs %}
{% if pub.year != current_year %}
<h3>{{ pub.year }}</h3>
{% assign current_year = pub.year %}
{% endif %}
<article class="archive__item" itemscope itemtype="http://schema.org/CreativeWork">
  <h2 class="archive__item-title" itemprop="headline">{{ pub.title }}</h2>
  <p class="archive__item-excerpt" itemprop="description">
    {{ pub.authors }} ({{ pub.year }}). <em>{{ pub.venue }}</em>.<br>
    {% if pub.citations %}<strong>Citations:</strong> {{ pub.citations }}<br>{% endif %}
    {% if pub.doi %}<strong>DOI:</strong> <a href="https://doi.org/{{ pub.doi }}">{{ pub.doi }}</a><br>{% endif %}
    {% if pub.url %}<strong>Link:</strong> <a href="{{ pub.url }}">{{ pub.url }}</a>{% endif %}
  </p>
</article>
{% endfor %}
