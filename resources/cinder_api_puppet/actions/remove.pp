class {'cinder::api':
  enabled            => false,
  package_ensure     => 'absent'
}
