module tcp
  use iso_c_binding, only: c_int, c_ptr, c_size_t, c_char, c_loc
  use error, only: get_error_message
  implicit none

  private
  public :: tcp_open, tcp_accept, tcp_read, tcp_write, tcp_try_close, tcp_close

  interface

    function c_tcp_open(port) result(socket) bind(c, name='c_tcp_open')
      import c_int
      integer(kind=c_int), intent(in), value :: port
      integer(kind=c_int) :: socket
    end function c_tcp_open

    function c_accept(socket) result(client) bind(c, name='c_tcp_accept')
      import c_int
      integer(kind=c_int), intent(in), value :: socket
      integer(kind=c_int) :: client
    end function c_accept

    function c_read(socket, buff, size) result(count) bind(c, name='c_tcp_read')
      import c_int, c_ptr, c_size_t
      integer(kind=c_int), intent(in), value :: socket
      type(c_ptr), intent(in), value :: buff
      integer(kind=c_int), intent(in), value :: size
      integer(kind=c_int) :: count
    end function c_read

    function c_write(socket, buff, size) result(count) bind(c, name='c_tcp_write')
      import c_int, c_ptr, c_size_t
      integer(kind=c_int), intent(in), value :: socket
      type(c_ptr), intent(in), value :: buff
      integer(kind=c_int), intent(in), value :: size
      integer(kind=c_int) :: count
    end function c_write

    function c_tcp_close(socket) result(err) bind(c, name='c_tcp_close')
      import c_int
      integer(kind=c_int), intent(in), value :: socket
      integer(kind=c_int) :: err
    end function c_tcp_close

  end interface

contains

  function tcp_open(port) result(socket)
    integer, intent(in) :: port
    integer :: socket

    socket = c_tcp_open(port)
  end function tcp_open

  function tcp_accept(socket) result(client)
    integer, intent(in) :: socket
    integer :: client

    client = c_accept(socket)
  end function tcp_accept

  function tcp_read(socket, buffer) result(readed)
    integer, intent(in) :: socket
    character(kind=c_char), dimension(:), intent(in), target :: buffer
    integer :: readed

    readed = c_read(socket, c_loc(buffer), size(buffer))
  end function tcp_read

  function tcp_write(socket, buffer) result(writed)
    integer, intent(in) :: socket
    character(kind=c_char), dimension(:), intent(in), target:: buffer
    integer :: writed

    writed = c_write(socket, c_loc(buffer), size(buffer))
  end function tcp_write

  function tcp_try_close(socket) result(err)
    integer, intent(in) :: socket
    integer :: err

    err = c_tcp_close(socket)
  end function tcp_try_close

  subroutine tcp_close(socket)
    integer, intent(in) :: socket
    integer :: dummy

    dummy = tcp_try_close(socket)
  end subroutine tcp_close
end module
