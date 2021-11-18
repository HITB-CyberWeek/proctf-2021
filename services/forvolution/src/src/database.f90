module database
  use iso_c_binding, only: c_int, c_ptr, c_char, c_loc, c_null_char
  use sha256, only: sha256_size
  use rand_helper, only: rand_fill_hex
  implicit none

  private
  
  public :: db_store, db_load, id_size

  integer, parameter :: id_size = 32

  interface
    function c_write(buffer, d, n) result(b) bind(c, name='c_db_write')
      import c_ptr, c_int
      type(c_ptr), intent(in), value :: buffer
      type(c_ptr), intent(in), value :: d
      integer(kind=c_int), intent(in), value :: n

      type(c_ptr) :: b
    end function c_write

    function c_store(start, finish, filename) result(r) bind(c, name='c_db_store')
      import c_ptr, c_char, c_int
      type(c_ptr), intent(in), value :: start
      type(c_ptr), intent(in), value :: finish
      type(c_ptr), intent(in), value :: filename

      integer(kind=c_int) :: r
    end function c_store
  end interface
contains

  function db_store(buffer, n, m, matrix, dlen, desc, key) result(id)
    character(kind=c_char), dimension(:), intent(in), target :: buffer
    integer(1), intent(in), target :: n
    integer(1), intent(in), target :: m
    integer(1), dimension(1:n, 1:m), intent(in), target :: matrix
    integer(1), intent(in), target :: dlen
    character, dimension(1:dlen), intent(in), target :: desc
    character, dimension(1:sha256_size), intent(in), target :: key

    character, dimension(1:id_size) :: id
    type(c_ptr) :: b
    integer(kind=c_int) :: res
    character(kind=c_char), dimension(:), allocatable, target :: filename

    call rand_fill_hex(id)
    b = c_loc(buffer)
    b = c_write(b, c_loc(key), sha256_size)
    b = c_write(b, c_loc(n), 1)
    b = c_write(b, c_loc(m), 1)
    b = c_write(b, c_loc(matrix), int(n) * m)
    b = c_write(b, c_loc(dlen), 1)
    b = c_write(b, c_loc(desc), int(dlen))

    filename = [(/'.', '/', 'd', 'b', '/'/), id, (/c_null_char/)]
    res = c_store(c_loc(buffer), b, c_loc(filename))

    if (res.eq.0) then
      id = achar(0)
    end if
  end function db_store

  subroutine db_load(id, n, m, matrix, dlen, desc, key)
    character, dimension(1:id_size), intent(in) :: id
    integer, intent(out) :: n
    integer, intent(out) :: m
    integer(1), dimension(:), intent(out) :: matrix
    integer, intent(out) :: dlen
    character, dimension(:), intent(out) :: desc
    character, dimension(1:sha256_size), intent(out) :: key

    n = 3
    m = 3
    matrix = (/1, 2, 3, 4, 5, 6, 7, 8, 9/)
    dlen = 4
    desc = (/'d', 'e', 's', 'c'/)
    key = 'x'
  end subroutine db_load

end module database
