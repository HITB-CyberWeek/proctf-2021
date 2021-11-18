program main
  use tcp_server, only: start
  use rand_helper, only: rand_init
  implicit none

  call rand_init()
  call start()
end program main
