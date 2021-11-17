module tcp_server
  use tcp, only: tcp_open, tcp_accept, tcp_close
  use epoll_wrapper, only: epoll, epoll_event
  use connection_handler, only: connection, connection_dead, connection_read
  use error, only: get_error_message
  implicit none

  private
  public :: start

  integer, parameter :: connection_pool_size = 10240

  type(connection), dimension(:), allocatable :: connection_pool

contains
  subroutine accept(socket, epfd)
    integer, intent(in) :: socket
    type(epoll), intent(inout) :: epfd
    integer :: client
    integer :: state

    state = connection_dead
    client = tcp_accept(socket)
    if (client .lt. 0) then
      return
    end if

    if (client .gt. connection_pool_size) then
      print *, "can't process fd ", client, '. Skip it'
      call tcp_close(client)
      return
    end if

    state = connection_pool(client)%init(client)
    if (state .ne. connection_dead) then
      if (epfd%add(client, state) .lt. 0) then
        print *, "can't add fd ", client, "to epoll. Skip it. Error: ", get_error_message()
        call tcp_close(client)
      end if
    end if
  end subroutine accept

  subroutine start
    integer :: socket, state, old_state, i
    type(epoll) :: epfd
    type(epoll_event), dimension(:), allocatable :: events
    type(epoll_event) :: event

    state = epfd%init(connection_pool_size)
    if (state .lt. 0) then
      print *, 'epoll create error:', get_error_message()
      call exit(1)
    end if

    allocate(connection_pool(0:connection_pool_size))

    socket = tcp_open(12345)
    print *, 'socket:', socket
    if (socket .lt. 0) then
      print *, 'open error: ', get_error_message()
      call exit(1)
    end if

    state = epfd%add(socket, connection_read)

    do
      events = epfd%wait()
      if (.not. allocated(events)) then
        print *, 'epoll wait error: ', get_error_message()
        call exit(1)
      end if
      do i = 1, size(events)
        event = events(i)
        if (event%socket .eq. socket) then
          if (event%mode .ne. connection_read) then
            print *, 'unexpected mode ', events(i)%mode, ' for server socket'
            call exit(1)
          end if
          call accept(socket, epfd)
        else
          old_state = connection_pool(event%socket)%connection_state
          state = connection_pool(event%socket)%handle(event%mode)
          if (state .eq. connection_dead .or. state .ne. old_state) then
            call epfd%update(event%socket, state)
          end if
        end if
      end do
    end do
  end subroutine start
end module tcp_server
