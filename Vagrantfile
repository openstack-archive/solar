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

Vagrant.require_version ">= 1.7.4"

require 'etc'
require 'log4r'
require 'yaml'

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"
HOME=Etc.getpwuid.dir
# Solar specific key paths mappings
INSECURE_KEY="#{HOME}/.vagrant.d/insecure_private_key"
KEY_PATH1="/vagrant/tmp/keys/ssh_private"
def get_machine_key (index = '')
  "/vagrant/.vagrant/machines/solar-dev#{index}/virtualbox/private_key"
end

# configs, custom updates _defaults
@logger = Log4r::Logger.new("vagrant::docker::driver")
defaults_cfg = YAML.load_file('vagrant-settings.yaml_defaults')
if File.exist?('vagrant-settings.yaml')
  custom_cfg = YAML.load_file('vagrant-settings.yaml')
  cfg = defaults_cfg.merge(custom_cfg)
else
  cfg = defaults_cfg
end

SLAVES_COUNT = cfg["slaves_count"]
SLAVES_RAM = cfg["slaves_ram"]
SLAVES_IPS = cfg["slaves_ips"]
SLAVES_IMAGE = cfg["slaves_image"]
SLAVES_IMAGE_VERSION = cfg["slaves_image_version"]
MASTER_RAM = cfg["master_ram"]
MASTER_IPS = cfg["master_ips"]
MASTER_IMAGE = cfg["master_image"]
MASTER_IMAGE_VERSION = cfg["master_image_version"]
SYNC_TYPE = cfg["sync_type"]
MASTER_CPUS = cfg["master_cpus"]
SLAVES_CPUS = cfg["slaves_cpus"]
PARAVIRT_PROVIDER = cfg.fetch('paravirtprovider', false)
PREPROVISIONED = cfg.fetch('preprovisioned', true)
DOCKER_MASTER_IMAGE=cfg['docker_master_image']
DOCKER_SLAVES_IMAGE=cfg['docker_slaves_image']
DOCKER_CMD=cfg['docker_cmd']
SOLAR_DB_BACKEND = cfg.fetch('solar_db_backend', 'riak')

# Initialize noop plugins only in case of PXE boot
require_relative 'bootstrap/vagrant_plugins/noop' unless PREPROVISIONED

# FIXME(bogdando) more natively to distinguish a provider specific logic
provider = (ARGV[2] || ENV['VAGRANT_DEFAULT_PROVIDER'] || :docker).to_sym

def ansible_playbook_command(filename, args=[])
  ansible_script_crafted = "ansible-playbook -v -i \"localhost,\" -c local /vagrant/bootstrap/playbooks/#{filename} #{args.join ' '}"
  @logger.info("Crafted ansible-script: #{ansible_script_crafted})")
  ansible_script_crafted
end

def shell_script(filename, args=[])
  shell_script_crafted = "/bin/bash #{filename} #{args.join ' '} 2>/dev/null"
  @logger.info("Crafted shell-script: #{shell_script_crafted})")
  shell_script_crafted
end

# W/a unimplemented docker-exec, see https://github.com/mitchellh/vagrant/issues/4179
# Use docker exec instead of the SSH provisioners
# TODO(bogdando) lxc-docker support (there is no exec)
def docker_exec (name, script)
  @logger.info("Executing docker-exec at #{name}: #{script}")
  system "docker exec -it #{name} #{script}"
end

solar_script = ansible_playbook_command("solar.yaml")
solar_agent_script = ansible_playbook_command("solar-agent.yaml")
master_pxe = ansible_playbook_command("pxe.yaml")

if provider == :docker
  # TODO(bogdando) use https://github.com/jpetazzo/pipework for multi net.
  # Hereafter, we will use only the 1st IP address and a single interface.
  # Also prepare docker volumes and workaround missing machines' ssh_keys
  # and virtualbox hardcoded paths in Solar
  key=get_machine_key
  docker_volumes = ["-v", "#{INSECURE_KEY}:#{KEY_PATH1}:ro"]
  docker_volumes << ["-v", "#{INSECURE_KEY}:#{key}:ro",
    "-v", "/sys/fs/cgroup:/sys/fs/cgroup",
    "-v", "/var/run/docker.sock:/var/run/docker.sock" ]
  SLAVES_COUNT.times do |i|
    index = i + 1
    key = get_machine_key index.to_s
    docker_volumes << ["-v", "#{INSECURE_KEY}:#{key}:ro"]
  end
  docker_volumes.flatten
  @logger.info("Crafted docker volumes: #{docker_volumes}")
end

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  if provider == :docker
    # W/a unimplemented docker networking, see
    # https://github.com/mitchellh/vagrant/issues/6667.
    # Create or delete the solar net (depends on the vagrant action)
    config.trigger.before :up do
      system <<-SCRIPT
      if ! docker network inspect solar >/dev/null 2>&1 ; then
        docker network create -d bridge \
          -o "com.docker.network.bridge.enable_icc"="true" \
          -o "com.docker.network.bridge.enable_ip_masquerade"="true" \
          -o "com.docker.network.driver.mtu"="1500" \
          --gateway=#{SLAVES_IPS[0]}1 \
          --ip-range=#{SLAVES_IPS[0]}0/24 \
          --subnet=#{SLAVES_IPS[0]}0/24 \
          solar >/dev/null 2>&1
      fi
      SCRIPT
    end
    config.trigger.after :destroy do
      system <<-SCRIPT
      docker network rm solar >/dev/null 2>&1
      SCRIPT
    end
    config.vm.provider :docker do |d, override|
      d.image = DOCKER_MASTER_IMAGE
      d.remains_running = false
      d.has_ssh = false
      d.cmd = DOCKER_CMD.split(' ')
    end
  else
    config.vm.box = MASTER_IMAGE
    config.vm.box_version = MASTER_IMAGE_VERSION
  end

  config.vm.define "solar-dev", primary: true do |config|
    config.vm.host_name = "solar-dev"
    if provider == :docker
      config.vm.provider :docker do |d, override|
        d.name = "solar-dev"
        d.create_args = ["-i", "-t", "--privileged", "--ip=#{MASTER_IPS[0]}", "--net=solar",
          docker_volumes].flatten
      end
      config.trigger.after :up, :option => { :vm => 'solar-dev'} do
        docker_exec("solar-dev","/usr/sbin/rsyslogd >/dev/null 2>&1")
        docker_exec("solar-dev","/usr/sbin/sshd >/dev/null 2>&1")
        docker_exec("solar-dev","#{solar_script} >/dev/null 2>&1")
        docker_exec("solar-dev","SOLAR_DB_BACKEND=#{SOLAR_DB_BACKEND} #{master_pxe} >/dev/null 2>&1") unless PREPROVISIONED
      end
    else
      # not the docker provider
      config.vm.provision "shell", inline: solar_script, privileged: true, env: {"SOLAR_DB_BACKEND": SOLAR_DB_BACKEND}
      config.vm.provision "shell", inline: master_pxe, privileged: true unless PREPROVISIONED
      config.vm.provision "file", source: INSECURE_KEY, destination: KEY_PATH1

      config.vm.provider :virtualbox do |v|
        v.memory = MASTER_RAM
        v.cpus = MASTER_CPUS
        v.customize [
          "modifyvm", :id,
          "--memory", MASTER_RAM,
          "--cpus", MASTER_CPUS,
          "--ioapic", "on",
        ]
        if PARAVIRT_PROVIDER
          v.customize ['modifyvm', :id, "--paravirtprovider", PARAVIRT_PROVIDER] # for linux guest
        end
        v.name = "solar-dev"
      end

      config.vm.provider :libvirt do |libvirt|
        libvirt.driver = 'kvm'
        libvirt.memory = MASTER_RAM
        libvirt.cpus = MASTER_CPUS
        libvirt.nested = true
        libvirt.cpu_mode = 'host-passthrough'
        libvirt.volume_cache = 'unsafe'
        libvirt.disk_bus = "virtio"
      end

      ind = 0
      MASTER_IPS.each do |ip|
        config.vm.network :private_network, ip: "#{ip}", :dev => "solbr#{ind}", :mode => 'nat'
        ind = ind + 1
      end

      if SYNC_TYPE == 'nfs'
        config.vm.synced_folder ".", "/vagrant", type: "nfs"
      end
      if SYNC_TYPE == 'rsync'
        config.vm.synced_folder ".", "/vagrant", type: "rsync",
          rsync__args: ["--verbose", "--archive", "--delete", "-z"]
      end
    end
  end

  SLAVES_COUNT.times do |i|
    index = i + 1
    ip_index = i + 3
    config.vm.define "solar-dev#{index}" do |config|
      config.vm.host_name = "solar-dev#{index}"
      if provider == :docker
        config.vm.provider :docker do |d, override|
          d.name = "solar-dev#{index}"
          d.image = DOCKER_SLAVES_IMAGE
          d.create_args = ["-i", "-t", "--privileged", "--ip=#{SLAVES_IPS[0]}#{ip_index}", "--net=solar",
            docker_volumes].flatten
        end
        config.trigger.after :up, :option => { :vm => "solar-dev#{index}" } do
          docker_exec("solar-dev#{index}","/usr/sbin/rsyslogd >/dev/null 2>&1")
          docker_exec("solar-dev#{index}","/usr/sbin/sshd >/dev/null 2>&1")
          docker_exec("solar-dev#{index}","#{solar_agent_script} >/dev/null 2>&1") if PREPROVISIONED
        end
      else
        # not the docker provider
        # Standard box with all stuff preinstalled
        config.vm.box = SLAVES_IMAGE
        config.vm.box_version = SLAVES_IMAGE_VERSION

        if PREPROVISIONED
          config.vm.provision "shell", inline: solar_agent_script, privileged: true
          #TODO(bogdando) figure out how to configure multiple interfaces when was not PREPROVISIONED
          ind = 0
          SLAVES_IPS.each do |ip|
            config.vm.network :private_network, ip: "#{ip}#{ip_index}", :dev => "solbr#{ind}", :mode => 'nat'
            ind = ind + 1
          end
        else
          # Disable attempts to install guest os and check that node is booted using ssh,
          # because nodes will have ip addresses from dhcp, and vagrant doesn't know
          # which ip to use to perform connection
          config.vm.communicator = :noop
          config.vm.guest = :noop_guest
          # Configure network to boot vm using pxe
          config.vm.network "private_network", adapter: 1, ip: "10.0.0.#{ip_index}"
          config.vbguest.no_install = true
          config.vbguest.auto_update = false
        end

        config.vm.provider :virtualbox do |v|
          boot_order(v, ['net', 'disk'])
          v.customize [
              "modifyvm", :id,
              "--memory", SLAVES_RAM,
              "--cpus", SLAVES_CPUS,
              "--ioapic", "on",
              "--macaddress1", "auto",
          ]
          if PARAVIRT_PROVIDER
            v.customize ['modifyvm', :id, "--paravirtprovider", PARAVIRT_PROVIDER] # for linux guest
          end
          v.name = "solar-dev#{index}"
        end

        config.vm.provider :libvirt do |libvirt|
          libvirt.driver = 'kvm'
          libvirt.memory = SLAVES_RAM
          libvirt.cpus = SLAVES_CPUS
          libvirt.nested = true
          libvirt.cpu_mode = 'host-passthrough'
          libvirt.volume_cache = 'unsafe'
          libvirt.disk_bus = "virtio"
        end

        if PREPROVISIONED
          if SYNC_TYPE == 'nfs'
            config.vm.synced_folder ".", "/vagrant", type: "nfs"
          end
          if SYNC_TYPE == 'rsync'
            config.vm.synced_folder ".", "/vagrant", type: "rsync",
            rsync__args: ["--verbose", "--archive", "--delete", "-z"]
          end
        end
      end
    end
  end
end


def boot_order(virt_config, order)
  # Boot order is specified with special flag:
  # --boot<1-4> none|floppy|dvd|disk|net
  4.times do |idx|
    device = order[idx] || 'none'
    virt_config.customize ['modifyvm', :id, "--boot#{idx + 1}", device]
  end
end
