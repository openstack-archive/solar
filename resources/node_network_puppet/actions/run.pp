$resource = hiera($::resource_name)
#TODO

class {'l23network':
  package_ensure    => $package_ensure,
}
