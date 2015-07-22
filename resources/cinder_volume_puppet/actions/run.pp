$resource = hiera($::resource_name)

$package_ensure    = $resource['input']['package_ensure']['value']
$enabled           = $resource['input']['enabled']['value']
$manage_service    = $resource['input']['manage_service']['value']

include cinder::params

package { 'cinder':
  ensure  => $package_ensure,
  name    => $::cinder::params::package_name,
} ->

class {'cinder::volume':
package_ensure    => $package_ensure,
enabled           => $enabled,
manage_service    => $manage_service,
}
