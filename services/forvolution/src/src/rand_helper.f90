module rand_helper
  implicit none

  private
  public :: rand_init, rand_fill_hex

contains
  subroutine rand_init()
    call random_init(.false., .false.)
  end subroutine

  subroutine rand_fill_hex(s)
    character, dimension(:), intent(out) :: s

    integer :: i

    do i = 1, size(s)
      s(i) = rand_hex()
    end do
  end subroutine

  function rand_hex() result(r)
    character :: r

    integer :: h
    real :: x

    call random_number(x)
    h = floor(16 * x)
    if (h.lt.10) then
      r = achar(h + 48)
    else
      r = achar(h + 97 - 10)
    end if
  end function rand_hex
end module rand_helper
