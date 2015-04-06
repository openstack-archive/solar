# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

init_script = <<SCRIPT
apt-get update
apt-get -y install python-pip python-dev
pip install ansible
ansible-playbook -i "localhost," -c local /vagrant/main.yml
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "deb/jessie-amd64"

  config.vm.provider "virtualbox" do |v|
    v.customize ["modifyvm", :id, "--memory", 2048]
  end

  config.vm.provision "shell", inline: init_script, privileged: true

  config.vm.define "solar-dev" do |guest1|
    guest1.vm.network "private_network", ip: "10.0.0.2"
  end

  config.vm.define "solar-dev2" do |guest2|
    guest2.vm.network "private_network", ip: "10.0.0.3"
  end

end
