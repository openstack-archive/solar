$resource = hiera($::resource_name)

$package_ensure    = $resource['input']['package_ensure']['value']

include cinder::params

package { 'cinder':
  ensure  => $package_ensure,
  name    => $::cinder::params::package_name,
} ->

class {'cinder::volume':
  package_ensure    => $package_ensure,
  enabled           => true,
  manage_service    => true,
}
