module connection_handler
  use iso_c_binding, only: c_char
  use tcp, only: tcp_read, tcp_write, tcp_close
  use database, only: db_store, db_load, id_size
  use string_utils, only: to_int, to_char
  use sha256, only: sha256_calc, sha256_size
  use matrix, only: convolution

  implicit none
  private
  public connection, connection_dead, connection_read, connection_write

  integer, parameter :: connection_dead = 0
  integer, parameter :: connection_read = 1
  integer, parameter :: connection_write = 2

  integer, parameter :: request_command = 0
  integer, parameter :: request_upload_size = 1
  integer, parameter :: request_upload = 2
  integer, parameter :: request_download_size = 3
  integer, parameter :: request_download = 4
  integer, parameter :: request_convolution_size = 5
  integer, parameter :: request_convolution = 6

  integer, parameter :: command_upload = 0
  integer, parameter :: command_download = 1
  integer, parameter :: command_convolution = 2

  integer, parameter :: ok = 0
  integer, parameter :: error_unknown_command = 1
  integer, parameter :: error_bad_size = 2
  integer, parameter :: error_unauthorized = 3
  integer, parameter :: error_exception = 255

  integer, parameter :: matrix_size = 100
  integer, parameter :: text_size = 255
  integer, parameter :: convolution_size = 9
  integer, parameter :: buffer_size = 4 * matrix_size ** 2 + text_size + text_size

  type :: extra_data
    integer :: n
    integer :: m
    integer :: desc
    integer :: key
  end type extra_data

  type :: connection
    integer, private :: socket
    character(kind=c_char), dimension(1:buffer_size), private :: buffer
    integer, private :: processed
    integer, private :: needed
    integer, public :: connection_state = connection_dead
    integer, private :: request_state = request_command
    type(extra_data), private :: extra
  contains
    procedure, public :: init
    procedure, public :: handle
    procedure, private :: handle_internal
    procedure, private :: handle_request
    procedure, private :: set_read
    procedure, private :: set_result
    procedure, private :: set_error
    procedure, private :: init_upload
    procedure, private :: handle_upload
    procedure, private :: init_download
    procedure, private :: handle_download
    procedure, private :: init_convolution
    procedure, private :: handle_convolution
  end type connection

contains

  function init(self, socket) result(state)
    class(connection), intent(inout) :: self
    integer, intent(in) :: socket
    integer :: state

    self%socket = socket
    call self%set_read(1)
    self%request_state = request_command
    state = self%connection_state
  end function init

  function handle(self, event_mode) result(state)
    class(connection), intent(inout) :: self
    integer, intent(in) :: event_mode
    integer :: state
    call handle_internal(self, event_mode)
    state = self%connection_state
  end function handle

  subroutine handle_internal(self, event_mode)
    class(connection), intent(inout) :: self
    integer, intent(in) :: event_mode
    integer :: new_processed

    if (event_mode .ne. self%connection_state) then
      call tcp_close(self%socket)
      self%connection_state = connection_dead
      return
    end if

    select case (self%connection_state)
      case(connection_read)
        new_processed = tcp_read(self%socket, self%needed - self%processed, self%buffer(self%processed + 1 : self%needed))
        if (new_processed .le. 0) then
          call tcp_close(self%socket)
          self%connection_state = connection_dead
          return
        end if

        self%processed = self%processed + new_processed
        if (self%processed .lt. self%needed) then
          return
        end if

        call self%handle_request()
      case(connection_write)
        new_processed = tcp_write(self%socket, self%needed - self%processed, self%buffer(self%processed + 1 : self%needed))
        if (new_processed .le. 0) then
          call tcp_close(self%socket)
          self%connection_state = connection_dead
          return
        end if

        self%processed = self%processed + new_processed
        if (self%processed .lt. self%needed) then
          return
        end if

        call self%set_read(1)
        self%request_state = request_command
    end select
  end subroutine handle_internal

  subroutine handle_request(self)
    class(connection), intent(inout) :: self

    select case(self%request_state)
      case(request_command)
        select case(iachar(self%buffer(1)))
          case(command_upload)
            call self%set_read(4)
            self%request_state = request_upload_size
          case(command_download)
            call self%set_read(1)
            self%request_state = request_download_size
          case(command_convolution)
            call self%set_read(2)
            self%request_state = request_convolution_size
          case default
            call self%set_error(error_unknown_command)
        end select
      case(request_upload_size)
        call self%init_upload()
      case(request_upload)
        call self%handle_upload()
      case(request_download_size)
        call self%init_download()
      case(request_download)
        call self%handle_download()
      case(request_convolution_size)
        call self%init_convolution()
      case(request_convolution)
        call self%handle_convolution()
    end select
  end subroutine handle_request

  subroutine set_read(self, size)
    class(connection), intent(inout) :: self
    integer :: size

    self%processed = 0
    self%needed = size
    self%connection_state = connection_read
  end subroutine set_read

  subroutine set_result(self, size, res)
    class(connection), intent(inout) :: self
    integer, intent(in) :: size
    character, dimension(1:size), intent(in) :: res

    self%processed = 0
    self%needed = size + 1
    self%buffer(1) = achar(ok)
    self%buffer(2:size+1) = res
    self%connection_state = connection_write
  end subroutine set_result

  subroutine set_error(self, error)
    class(connection), intent(inout) :: self
    integer :: error

    self%processed = 0
    self%needed = 1
    self%buffer(1:1) = achar(error)
    self%connection_state = connection_write
  end subroutine set_error

  subroutine init_upload(self)
    class(connection), intent(inout) :: self
    integer :: n
    integer :: m
    integer :: desc
    integer :: key

    n = iachar(self%buffer(1))
    m = iachar(self%buffer(2))
    desc = iachar(self%buffer(3))
    key = iachar(self%buffer(4))

    if (n.le.0.or.m.le.0.or.desc.le.0.or.key.le.0) then
      call self%set_error(error_bad_size)
      return
    end if

    if ((n.gt.matrix_size).or.(m.gt.matrix_size)) then
      call self%set_error(error_bad_size)
      return
    end if

    self%extra%n = n
    self%extra%m = m
    self%extra%desc = desc
    self%extra%key = key
    call self%set_read(n * m + desc + key)
    self%request_state = request_upload
  end subroutine init_upload

  subroutine handle_upload(self)
    class(connection), intent(inout) :: self

    integer :: n
    integer :: m
    integer :: ndesc
    integer :: key
    character, dimension(1:id_size) :: id
    character, dimension(1:sha256_size) :: key_hash
    integer(1), dimension(:,:), allocatable :: matrix
    character, dimension(:), allocatable :: desc

    n = self%extra%n
    m = self%extra%m
    ndesc = self%extra%desc
    key = self%extra%key

    matrix = reshape(to_int(self%buffer(1:n*m)), (/n, m/))
    desc = self%buffer(n*m+1:n*m+ndesc)

    key_hash = sha256_calc(self%buffer(n*m+ndesc+1:n*m+ndesc+key))

    id = db_store(self%buffer, int(n, 1), int(m, 1), matrix, int(ndesc, 1), desc, key_hash)

    if (id(1).eq.achar(0)) then
      call self%set_error(error_exception)
    else
      call self%set_result(id_size, id)
    end if
  end subroutine handle_upload

  subroutine init_download(self)
    class(connection), intent(inout) :: self
    integer :: key

    key = iachar(self%buffer(1))
    if (key.le.0) then
      call self%set_error(error_bad_size)
      return
    end if

    self%extra%key = key

    call self%set_read(key + id_size)
    self%request_state = request_download
  end subroutine init_download

  subroutine handle_download(self)
    class(connection), intent(inout) :: self

    integer :: lkey
    integer(1), pointer :: n
    integer(1), pointer :: m
    integer(1), dimension(:,:), pointer :: matrix
    integer(1), pointer :: ndesc
    character, dimension(:), pointer :: desc
    character, dimension(:), pointer :: stored_key_hash
    character, dimension(1:sha256_size) :: key_hash
    character, dimension(:), allocatable :: id
    logical :: success

    lkey = self%extra%key
    id = self%buffer(1:id_size)
    key_hash = sha256_calc(self%buffer(id_size+1:id_size+lkey))

    success = db_load(self%buffer, id, n, m, matrix, ndesc, desc, stored_key_hash)
    if (.not.success) then
      call self%set_error(error_exception)
      return
    end if
    if (size(stored_key_hash).ne.sha256_size.or.any(key_hash.ne.stored_key_hash)) then
      call self%set_error(error_unauthorized)
      return
    end if

    self%processed = 0
    self%needed = 4 + n * m + ndesc
    self%buffer(1) = achar(ok)
    self%buffer(2) = achar(n)
    self%buffer(3) = achar(m)
    self%buffer(4) = achar(ndesc)
    self%buffer(5:5+int(n)*m-1) = transfer(matrix, self%buffer(5:5+n*m-1))
    self%buffer(5+int(n)*m:5+n*m+ndesc-1) = desc(1:ndesc)
    self%connection_state = connection_write
  end subroutine

  subroutine init_convolution(self)
    class(connection), intent(inout) :: self
    integer :: n
    integer :: m

    n = iachar(self%buffer(1))
    m = iachar(self%buffer(2))

    if ((n.gt.convolution_size).or.(m.gt.convolution_size)) then
      call self%set_error(error_bad_size)
      return
    end if

    self%extra%n = n
    self%extra%m = m
    call self%set_read(id_size + n * m)
    self%request_state = request_convolution
  end subroutine init_convolution

  subroutine handle_convolution(self)
    class(connection), intent(inout) :: self

    integer :: kn
    integer :: km

    integer(1), pointer :: n
    integer(1), pointer :: m
    integer(1), dimension(:,:), pointer :: matrix
    integer(1), pointer :: ndesc
    character, dimension(:), pointer :: desc
    character, dimension(:), pointer :: stored_key_hash
    integer, dimension(:,:), allocatable :: res

    logical :: success
    character, dimension(:), allocatable :: id
    integer(1), dimension(:,:), allocatable :: kernel
    integer, dimension(1:2) :: rsize

    kn = self%extra%n
    km = self%extra%m

    id = self%buffer(1:id_size)
    kernel = reshape(to_int(self%buffer(id_size + 1: id_size + kn * km)), (/kn, km/))

    success = db_load(self%buffer, id, n, m, matrix, ndesc, desc, stored_key_hash)
    if (.not.success) then
      call self%set_error(error_exception)
      return
    end if

    if (kn.gt.n.or.km.gt.m) then
      call self%set_error(error_bad_size)
      return
    end if

    res = convolution(matrix, kernel)
    rsize = shape(res)

    self%processed = 0
    self%needed = 3+ 4 * n * m
    self%buffer(1) = achar(ok)
    self%buffer(2) = achar(n)
    self%buffer(3) = achar(m)
    self%buffer(4:4+4*size(res)-1) = transfer(res, self%buffer(1), size(res) * 4)
    self%connection_state = connection_write
  end subroutine handle_convolution

end module connection_handler
