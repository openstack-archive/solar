# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

init_script = <<SCRIPT
apt-get update
apt-get -y install python-pip python-dev
pip install ansible
ansible-playbook -i "localhost," -c local /vagrant/main.yml /vagrant/docker.yml
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "deb/jessie-amd64"
  #rustyrobot/deb-jessie-amd64"

  config.vm.define "solar-dev", primary: true do |guest1|
    guest1.vm.provision "shell", inline: init_script, privileged: true
    guest1.vm.provision "file", source: "~/.vagrant.d/insecure_private_key", destination: "/vagrant/tmp/keys/ssh_private"
    guest1.vm.provision "file", source: "ansible.cfg", destination: "/home/vagrant/.ansible.cfg"
    guest1.vm.network "private_network", ip: "10.0.0.2"
    guest1.vm.host_name = "solar-dev"

    guest1.vm.provider :virtualbox do |v|
      v.customize ["modifyvm", :id, "--memory", 256]
      v.name = "solar-dev"
    end
  end

  config.vm.define "solar-dev2" do |guest2|
    guest2.vm.provision "shell", inline: init_script, privileged: true
    guest2.vm.network "private_network", ip: "10.0.0.3"
    guest2.vm.host_name = "solar-dev2"

    guest2.vm.provider :virtualbox do |v|
      v.customize ["modifyvm", :id, "--memory", 1024]
      v.name = "solar-dev2"
    end
  end

  config.vm.define "solar-dev3" do |guest3|
    guest3.vm.provision "shell", inline: init_script, privileged: true
    guest3.vm.network "private_network", ip: "10.0.0.4"
    guest3.vm.host_name = "solar-dev3"

    guest3.vm.provider :virtualbox do |v|
      v.customize ["modifyvm", :id, "--memory", 1024]
      v.name = "solar-dev3"
    end
  end

  config.vm.define "solar-dev4" do |guest4|
    guest4.vm.provision "shell", inline: init_script, privileged: true
    guest4.vm.network "private_network", ip: "10.0.0.5"
    guest4.vm.host_name = "solar-dev4"

    guest4.vm.provider :virtualbox do |v|
      v.customize ["modifyvm", :id, "--memory", 1024]
      v.name = "solar-dev4"
    end
  end
end
