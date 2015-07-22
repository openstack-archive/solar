$resource = hiera($::resource_name)

$scheduler_driver  = $resource['input']['scheduler_driver']['value']
$package_ensure    = $resource['input']['package_ensure']['value']
$enabled           = $resource['input']['enabled']['value']
$manage_service    = $resource['input']['manage_service']['value']

include cinder::params

package { 'cinder':
  ensure  => $package_ensure,
  name    => $::cinder::params::package_name,
} ->

class {'cinder::scheduler':
scheduler_driver  => $scheduler_driver,
package_ensure    => $package_ensure,
enabled           => $enabled,
manage_service    => $manage_service,
}
