class { 'nova::api':
  ensure_package => 'absent',
  enabled        => false,
}
