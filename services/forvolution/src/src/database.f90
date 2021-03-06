module database
  use iso_c_binding, only: c_int, c_ptr, c_char, c_loc, c_f_pointer, c_null_char
  use sha256, only: sha256_size
  use rand_helper, only: rand_fill_hex
  use string_utils, only: to_array, is_hex
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
      import c_ptr, c_int
      type(c_ptr), intent(in), value :: start
      type(c_ptr), intent(in), value :: finish
      type(c_ptr), intent(in), value :: filename

      integer(kind=c_int) :: r
    end function c_store

    function c_load(buffer, n, filename) result(r) bind(c, name='c_db_load')
      import c_ptr, c_int
      type(c_ptr), intent(in), value :: buffer
      integer(kind=c_int), intent(in), value :: n
      type(c_ptr), intent(in), value :: filename

      integer(kind=c_int) :: r
    end function c_load

    function c_shift(buffer, n) result(r) bind(c, name='c_db_shift')
      import c_ptr, c_int
      type(c_ptr), intent(in), value :: buffer
      integer(kind=c_int), intent(in), value :: n

      type(c_ptr) :: r
    end function c_shift
  end interface
contains

  function db_store(buffer, matrix, desc, key) result(id)
    character(kind=c_char), dimension(:), intent(in), target :: buffer
    integer(1), dimension(:,:), intent(in), target :: matrix
    character(kind=c_char), dimension(:), intent(in), target :: desc
    character(kind=c_char), dimension(1:sha256_size), intent(in), target :: key

    integer(1), dimension(1:2), target :: nsize
    integer(1), target :: dsize
    character, dimension(1:id_size) :: id
    type(c_ptr) :: b
    integer(kind=c_int) :: res
    character(kind=c_char), dimension(:), allocatable, target :: filename

    nsize = shape(matrix)
    dsize = int(size(desc), 1)
    call rand_fill_hex(id)
    b = c_loc(buffer)
    b = c_write(b, c_loc(key), sha256_size)
    b = c_write(b, c_loc(nsize), 2)
    b = c_write(b, c_loc(matrix), size(matrix))
    b = c_write(b, c_loc(dsize), 1)
    b = c_write(b, c_loc(desc), int(dsize))

    filename = get_name(id)
    res = c_store(c_loc(buffer), b, c_loc(filename))

    if (res.eq.0) then
      id = achar(0)
    end if
  end function db_store

  function db_load(buffer, id, matrix, desc, key) result(r)
    character(kind=c_char), dimension(:), intent(in), target :: buffer
    character, dimension(1:id_size), intent(in) :: id
    integer(1), dimension(:,:), intent(in), pointer :: matrix
    character(kind=c_char), dimension(:), intent(in), pointer :: desc
    character(kind=c_char), dimension(:), intent(in), pointer :: key

    logical :: r

    integer(1), pointer :: n
    integer(1), pointer :: m
    integer(1), pointer :: dsize
    character(kind=c_char), dimension(:), allocatable, target :: filename
    type(c_ptr) :: b
    integer :: have

    if(any(.not.is_hex(id))) then
      r = .false.
      return
    end if

    filename = get_name(id)
    b = c_loc(buffer)
    have = c_load(b, size(buffer), c_loc(filename))

    have = have - sha256_size
    if (have.lt.0) then
      r = .false.
      return
    end if
    call c_f_pointer(b, key, (/sha256_size/))
    b = c_shift(b, sha256_size)

    have = have - 1
    if (have.lt.0) then
      r = .false.
      return
    end if
    call c_f_pointer(b, n)
    b = c_shift(b, 1)

    have = have - 1
    if (have.lt.0) then
      r = .false.
      return
    end if
    call c_f_pointer(b, m)
    b = c_shift(b, 1)

    have = have - int(n) * int(m)
    if (have.lt.0) then
      r = .false.
      return
    end if
    call c_f_pointer(b, matrix, (/n, m/))
    b = c_shift(b, int(n) * int(m))

    have = have - 1
    if (have.lt.0) then
      r = .false.
      return
    end if
    call c_f_pointer(b, dsize)
    b = c_shift(b, 1)

    have = have - int(dsize)
    if (have.lt.0) then
      r = .false.
      return
    end if
    call c_f_pointer(b, desc, (/int(dsize)/))

    r = .true.
  end function db_load

  function get_name(id) result(filename)
    character, dimension(1:id_size), intent(in) :: id

    character, dimension(:), allocatable :: filename

    filename = [to_array('db/'), id(1:2), (/'/'/), id(3:), (/c_null_char/)]
  end function get_name

end module database
