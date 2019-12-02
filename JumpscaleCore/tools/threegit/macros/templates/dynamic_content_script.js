callActorAndRender('{{ actor }}', '{{ method }}', {{ args | safe }}, '{{ container_id }}', {% if markdown %}true{% else %} false{% endif %});
