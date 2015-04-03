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
    v.name = "solar-dev"
  end

  config.vm.provision "shell", inline: init_script, privileged: true

end
