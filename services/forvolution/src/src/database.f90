module database
  use sha256, only: sha256_size
  implicit none

  private
  
  public :: db_store, db_load, id_size

  integer, parameter :: id_size = 16

contains
  
  function db_store(n, m, matrix, dlen, desc, key) result(id)
    integer, intent(in) :: n
    integer, intent(in) :: m
    integer(1), dimension(1:n*m), intent(in) :: matrix
    integer, intent(in) :: dlen
    character, dimension(1:dlen), intent(in) :: desc
    character, dimension(1:sha256_size), intent(in) :: key

    character, dimension(1:id_size) :: id

    print *, 'matrix: (', n, 'x', m, ')'
    print *, matrix
    print *, 'desc: "', desc, '"'
    print *, 'key: "', key, '"'

    id = (/'n','u','l','l','_','i','d','_','i','s','_','e','m','p','t','y'/)
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
