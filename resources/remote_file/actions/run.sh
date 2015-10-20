mkdir -p {{dest}}

{% for transport in remote %}
    {% if transport.name == 'ssh' %}
scp -i {{transport.key}} -r {{transport.user}}@{{remote_ip}}:/{{remote_path}} {{dest}}
exit 0
    {% endif %}
{% endfor %}
echo 'No suitable transport.'
exit 2
