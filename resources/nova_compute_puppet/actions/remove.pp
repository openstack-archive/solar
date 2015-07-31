class { 'nova::compute':
  ensure_package => 'absent',
  enabled        => false,
}