# Noop Vagrant plugins are used in case if Vagrant does not
# have an access to VMs (e.g. there is no information about ip),
# so it just runs VMs and does not try to perform additional
# actions using SSH.

class NoopCommunicator < Vagrant.plugin("2", :communicator)

  def ready?
    true
  end

  def wait_for_ready(timeout)
    true
  end

end


class NoopGuest < Vagrant.plugin("2", :guest)

  def self.change_host_name(*args)
    true
  end

  def self.configure_networks(*args)
    true
  end

  def self.mount_virtualbox_shared_folder(*args)
    true
  end

end


class NoopCommunicatorPlugin < Vagrant.plugin("2")

  name 'Noop communicator/guest'
  description 'Noop communicator/guest'

  communicator('noop') do
    NoopCommunicator
  end

  guest 'noop_guest' do
    NoopGuest
  end

  guest_capability 'noop_guest', 'change_host_name' do
    NoopGuest
  end

  guest_capability 'noop_guest', 'configure_networks' do
    NoopGuest
  end

  guest_capability 'noop_guest', 'mount_virtualbox_shared_folder' do
    NoopGuest
  end

end
