module string_utils
  use iso_c_binding, only: c_null_char, c_ptr, c_char, c_size_t, c_f_pointer
  implicit none

  private
  public from_c_string, to_int, to_string, to_array, parse_int, is_hex
 
interface from_c_string
  module procedure from_c_ptr, from_c_nptr
end interface from_c_string

interface to_array
  module procedure to_array_string, to_array_integer, to_array_integer_1
end interface

contains
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

  function to_string(ar, len) result(r)
    character, dimension(:), intent(in) :: ar
    integer, intent(in) :: len
    character(len=len) :: r

    integer :: i
    integer :: n

    if (len.le.size(ar)) then
      n = len
    else
      n = size(ar)
    end if

    do i = 1, n
      r(i:i) = ar(i)
    end do
  end function to_string

  function to_array_string(s) result(r)
    character(len=*), intent(in) :: s
    character, dimension(:), allocatable :: r

    integer :: i

    allocate(r(1:len(s)))

    do i = 1, len(s)
      r(i) = s(i:i)
    end do
  end function to_array_string

  function to_array_integer(a) result(r)
    integer, intent(in) :: a
    character, dimension(:), allocatable :: r

    integer :: len
    integer :: aa

    if (a.eq.0) then
      r = (/'0'/)
      return
    end if

    len = 0
    aa = a
    do while (aa.gt.0)
      aa = aa / 10
      len = len + 1
    end do

    allocate(r(1:len))

    aa = a
    do while (aa.gt.0)
      r(len) = char(mod(aa, 10) + 48)
      aa = aa / 10
      len = len - 1
    end do
  end function to_array_integer

  function to_array_integer_1(a) result(r)
    integer(1), intent(in) :: a
    character, dimension(:), allocatable :: r

    r = to_array_integer(int(a))
  end function to_array_integer_1

  function parse_int(s) result(r)
    character, dimension(:), intent(in) :: s
    integer(1) :: r

    integer :: i

    r = 0
    do i = 1, size(s)
      r = r * 10_1 + iachar(s(i)) - 48_1
    end do
  end function parse_int

  elemental function is_hex(ch) result(r)
    character, intent(in) :: ch
    logical :: r

    r = 'a'.le.ch.and.ch.le.'f'.or.'0'.le.ch.and.ch.le.'9'
  end function is_hex

end module string_utils
