module matrix
  implicit none

  private

  public expand, convolution

contains
  function expand(n, m, matrix, k) result(r)
    integer, intent(in) :: n
    integer, intent(in) :: m
    integer(1), dimension(1:n, 1:m), intent(in) :: matrix
    integer, intent(in) :: k
    integer(1), dimension(1:n+k-1, 1:m+k-1) :: r

    integer :: p

    p = k / 2
    r(:,:) = 0
    r(p+1:n+p, p+1:m+p) = matrix(1:n,1:m)
  end function expand

  function convolution(n, m, matrix, k, kernel) result(r)
    integer, intent(in) :: n
    integer, intent(in) :: m
    integer, intent(in) :: k
    integer(1), dimension(1 : n + k - 1, 1 : m + k - 1), intent(in) :: matrix
    integer(1), dimension(1:k, 1:k), intent(in) :: kernel
    integer(4), dimension(1:n, 1:m) :: r

    integer :: i
    integer :: j

    do j = 1, m
      do i = 1, n
        r(i, j) = sum(matrix(i:i+k-1, j:j+k-1) * int(kernel))
      end do
    end do
  end function convolution
end module matrix
