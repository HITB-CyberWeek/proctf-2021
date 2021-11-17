module error
  use iso_c_binding, only: c_int, c_ptr, c_bool
  use string_utils, only: from_c_string
  implicit none

  private
  public :: get_errno, get_error_message

  interface
    function c_get_errno() result(errno) bind(c, name='c_get_errno')
      import c_int
      integer(kind=c_int) :: errno
    end function c_get_errno

    function c_get_error_message() result(message) bind(c, name='c_get_error_message')
      import c_ptr
      type(c_ptr) :: message
    end function c_get_error_message
  end interface

contains
  function get_errno() result(errno)
    integer :: errno
    errno = c_get_errno()
  end function get_errno

  function get_error_message() result(message)
    character(:), allocatable :: message
    message = from_c_string(c_get_error_message())
  end function get_error_message

end module error
