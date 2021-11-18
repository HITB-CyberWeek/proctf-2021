module string_utils
  use iso_c_binding, only: c_null_char, c_ptr, c_char, c_size_t, c_f_pointer
  implicit none

  private
  public :: from_c_string, to_int, to_char
 
interface from_c_string
  module procedure from_c_string, from_c_ptr, from_c_nptr
end interface from_c_string

contains
  function from_c_string(c_str) result(f_str)
    character(len=1), intent(in) :: c_str(:)
    character(:), allocatable :: f_str
    integer i, len

    len = 0
    do while (c_str(len + 1) .ne. c_null_char)
      len = len + 1
    end do

    allocate(character(len) :: f_str)
    do i = 1, len
      f_str(i:i) = c_str(i)
    end do
  end function from_c_string

  function from_c_ptr(ptr) result(f_str)
    type(c_ptr), intent(in), value :: ptr
    character(len=:, kind=c_char), allocatable :: f_str

    interface
      function c_strlen(s) result(l) bind(c, name='strlen')
        import c_ptr, c_size_t
        type(c_ptr), intent(in), value :: s
        integer(kind=c_size_t) :: l
      end function c_strlen
    end interface

    f_str = from_c_nptr(ptr, c_strlen(ptr))
  end function from_c_ptr

  function from_c_nptr(ptr, n) result(f_str)
    type(c_ptr), intent(in), value :: ptr
    integer(kind=c_size_t), intent(in) :: n
    character(len=n, kind=c_char) :: f_str
    character(len=n, kind=c_char), pointer :: s_ptr

    call c_f_pointer(ptr, s_ptr)
    f_str = s_ptr
  end function from_c_nptr

  elemental function to_int(ch) result(r)
    character(kind=c_char), intent(in) :: ch
    integer(1) :: r
    r = transfer(ch, r)
  end function to_int

  elemental function to_char(i) result(r)
    integer(1), intent(in) :: i
    character :: r
    r = transfer(i, r)
  end function to_char

end module string_utils