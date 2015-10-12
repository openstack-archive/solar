mkdir -p {{remote_path}}

scp -i {{remote_key}} -r {{remote_user}}@{{remote_ip}}:/{{remote_path}} {{dest}}
