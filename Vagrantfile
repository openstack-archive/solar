# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"
SLAVES_COUNT = 2

init_script = <<SCRIPT
apt-get update
apt-get -y install python-pip python-dev
pip install ansible
ansible-playbook -i "localhost," -c local /vagrant/main.yml /vagrant/docker.yml
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "deb/jessie-amd64"

  config.vm.define "solar-dev", primary: true do |config|
    config.vm.provision "shell", inline: init_script, privileged: true
    config.vm.provision "file", source: "~/.vagrant.d/insecure_private_key", destination: "/vagrant/tmp/keys/ssh_private"
    config.vm.provision "file", source: "ansible.cfg", destination: "/home/vagrant/.ansible.cfg"
    config.vm.network "private_network", ip: "10.0.0.2"
    config.vm.host_name = "solar-dev"

    config.vm.provider :virtualbox do |v|
      v.customize ["modifyvm", :id, "--memory", 1024]
      v.name = "solar-dev"
    end
  end

  SLAVES_COUNT.times do |i|
    index = i + 1
    ip_index = i + 2
    config.vm.define "solar-dev#{index}" do |config|
      config.vm.provision "shell", inline: init_script, privileged: true
      config.vm.network "private_network", ip: "10.0.0.#{ip_index}"
      config.vm.host_name = "solar-dev#{index}"

      config.vm.provider :virtualbox do |v|
        v.customize ["modifyvm", :id, "--memory", 256]
        v.name = "solar-dev#{index}"
      end
    end
  end

end
