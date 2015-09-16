# -*- mode: ruby -*-
# vi: set ft=ruby :
#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

require 'yaml'

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

# configs, custom updates _defaults
defaults_cfg = YAML.load_file('vagrant-settings.yaml_defaults')
if File.exist?('vagrant-settings.yaml')
  custom_cfg = YAML.load_file('vagrant-settings.yaml')
  cfg = defaults_cfg.merge(custom_cfg)
else
  cfg = defaults_cfg
end

SLAVES_COUNT = cfg["slaves_count"]
SLAVES_RAM = cfg["slaves_ram"]
MASTER_RAM = cfg["master_ram"]
SYNC_TYPE = cfg["sync_type"]

def ansible_playbook_command(filename, args=[])
  "ansible-playbook -v -i \"localhost,\" -c local /vagrant/bootstrap/playbooks/#{filename} #{args.join ' '}"
end

solar_script = ansible_playbook_command("solar.yaml")

slave_script = ansible_playbook_command("custom-configs.yaml", ["-e", "master_ip=10.0.0.2"])

master_celery = ansible_playbook_command("celery.yaml", ["--skip-tags", "slave"])

slave_celery = ansible_playbook_command("celery.yaml", ["--skip-tags", "master"])

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.define "solar-dev", primary: true do |config|
    config.vm.box = "cgenie/solar-master"

    config.vm.provision "shell", inline: solar_script, privileged: true
    config.vm.provision "shell", inline: master_celery, privileged: true
    config.vm.provision "file", source: "~/.vagrant.d/insecure_private_key", destination: "/vagrant/tmp/keys/ssh_private"
    config.vm.provision "file", source: "bootstrap/ansible.cfg", destination: "/home/vagrant/.ansible.cfg"
    config.vm.network "private_network", ip: "10.0.0.2"
    config.vm.host_name = "solar-dev"

    config.vm.provider :virtualbox do |v|
      v.customize [
        "modifyvm", :id,
        "--memory", MASTER_RAM,
        "--paravirtprovider", "kvm" # for linux guest
      ]
      v.name = "solar-dev"
    end

    config.vm.provider :libvirt do |libvirt|
      libvirt.driver = 'kvm'
      libvirt.memory = MASTER_RAM
      libvirt.nested = true
      libvirt.cpu_mode = 'host-passthrough'
      libvirt.volume_cache = 'unsafe'
    end

    if SYNC_TYPE == 'nfs'
      config.vm.synced_folder ".", "/vagrant", type: "nfs"
    end
    if SYNC_TYPE == 'rsync'
      config.vm.synced_folder ".", "/vagrant", rsync: "nfs",
        rsync__args: ["--verbose", "--archive", "--delete", "-z"]
    end
  end

  SLAVES_COUNT.times do |i|
    index = i + 1
    ip_index = i + 3
    config.vm.define "solar-dev#{index}" do |config|
      # standard box with all stuff preinstalled
      config.vm.box = "cgenie/solar-master"

      config.vm.provision "file", source: "bootstrap/ansible.cfg", destination: "/home/vagrant/.ansible.cfg"
      config.vm.provision "shell", inline: slave_script, privileged: true
      config.vm.provision "shell", inline: solar_script, privileged: true
      config.vm.provision "shell", inline: slave_celery, privileged: true
      config.vm.network "private_network", ip: "10.0.0.#{ip_index}"
      config.vm.host_name = "solar-dev#{index}"

      config.vm.provider :virtualbox do |v|
        v.customize [
            "modifyvm", :id,
            "--memory", SLAVES_RAM,
            "--paravirtprovider", "kvm" # for linux guest
        ]
        v.name = "solar-dev#{index}"
      end

      config.vm.provider :libvirt do |libvirt|
        libvirt.driver = 'kvm'
        libvirt.memory = SLAVES_RAM
        libvirt.nested = true
        libvirt.cpu_mode = 'host-passthrough'
        libvirt.volume_cache = 'unsafe'
      end

      if SYNC_TYPE == 'nfs'
        config.vm.synced_folder ".", "/vagrant", type: "nfs"
      end
      if SYNC_TYPE == 'rsync'
        config.vm.synced_folder ".", "/vagrant", rsync: "nfs",
          rsync__args: ["--verbose", "--archive", "--delete", "-z"]
      end
    end
  end

end
