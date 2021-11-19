module matrix
  implicit none

  private

  public convolution

contains
  function convolution(matrix, kernel) result(r)
    integer(1), dimension(:,:), intent(in) :: matrix
    integer(1), dimension(:,:), intent(in) :: kernel

    integer(4), dimension(:,:), allocatable :: r

    integer :: i
    integer :: j
    integer, dimension(1:2) :: msize
    integer, dimension(1:2) :: ksize
    integer, dimension(1:2) :: rsize

    msize = shape(matrix)
    ksize = shape(kernel)
    allocate(r(1:msize(1)-ksize(1)+1, 1:msize(2)-ksize(1)+1))
    rsize = shape(r)

    do j = 1, rsize(2)
      do i = 1, rsize(1)
        r(i, j) = sum(matrix(i:i+ksize(1)-1, j:j+ksize(2)-1) * int(kernel))
      end do
    end do
  end function convolution
end module matrix
