module connection_handler
  use iso_c_binding, only: c_char
  use tcp, only: tcp_read, tcp_write, tcp_close
  use database, only: db_store, db_load, id_size
  use string_utils, only: to_int, to_string, parse_int, to_array
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

  character, parameter :: delimiter = ';'

  integer, parameter :: command_minimal_length = 6
  integer, parameter :: command_length = 11
  character(len=6), parameter :: command_upload = 'UPLOAD'
  character(len=8), parameter :: command_download = 'DOWNLOAD'
  character(len=11), parameter :: command_convolution = 'CONVOLUTION'

  character(len=2), parameter :: ok = 'ok'

  integer, parameter :: matrix_size = 35
  integer, parameter :: text_size = 99
  integer, parameter :: convolution_size = 10
  integer, parameter :: buffer_size = 4 * matrix_size ** 2 + text_size + text_size

  type :: extra_data
    integer :: n
    integer :: m
    integer :: desc
    integer :: key
  end type extra_data

  type :: connection
    character(kind=c_char), dimension(1:buffer_size), private :: buffer
    integer, private :: processed
    integer, private :: needed_bytes
    integer, private :: needed_fields
    integer, private :: bytes_limit

    integer, private :: socket
    integer, public :: connection_state = connection_dead
    integer, private :: request_state = request_command
    type(extra_data), private :: extra
  contains
    procedure, public :: init
    procedure, public :: handle
    procedure, private :: handle_internal
    procedure, private :: handle_request
    procedure, private :: set_read_bytes
    procedure, private :: set_read_fields
    procedure, private :: set_error
    procedure, private :: add_to_response
    procedure, private :: add_to_response_str
    procedure, private :: add_to_response_int
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
    call self%set_read_fields(command_minimal_length+1, command_length+1, 1)
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
    integer :: fields

    if (event_mode.ne.self%connection_state) then
      call tcp_close(self%socket)
      self%connection_state = connection_dead
      return
    end if

    select case (self%connection_state)
      case(connection_read)
        new_processed = tcp_read(self%socket, self%buffer(self%processed + 1 : self%needed_bytes))
        if (new_processed.le.0) then
          call tcp_close(self%socket)
          self%connection_state = connection_dead
          return
        end if

        self%processed = self%processed + new_processed

        if (self%needed_fields.gt.0) then
          fields = count(self%buffer(1:self%processed).eq.delimiter)
          if (fields.ge.self%needed_fields) then
            call self%handle_request()
          elseif (self%needed_bytes.ge.self%bytes_limit) then
            call self%set_error('problem with fields parsing')
          else
            self%needed_bytes = self%needed_bytes + 1
          end if
          return
        end if

        if (self%processed.ge.self%needed_bytes) then
          call self%handle_request()
        end if
      case(connection_write)
        new_processed = tcp_write(self%socket, self%buffer(self%processed + 1 : self%needed_bytes))
        if (new_processed.le.0) then
          call tcp_close(self%socket)
          self%connection_state = connection_dead
          return
        end if

        self%processed = self%processed + new_processed
        if (self%processed.lt.self%needed_bytes) then
          return
        end if

        call self%set_read_fields(command_minimal_length+1, command_length+1, 1)
        self%request_state = request_command
    end select
  end subroutine handle_internal

  subroutine handle_request(self)
    class(connection), intent(inout) :: self

    character(len=command_length) :: command

    select case(self%request_state)
      case(request_command)
        command = to_string(self%buffer(1:self%processed-1), self%processed-1)
        if (command.eq.command_upload) then
          call self%set_read_fields(2 * 4, 3 * 4, 4)
          self%request_state = request_upload_size
        elseif (command.eq.command_download) then
          call self%set_read_fields(2 * 1, 3 * 1, 1)
          self%request_state = request_download_size
        elseif (command.eq.command_convolution) then
          call self%set_read_fields(2 * 2, 3 * 2, 2)
          self%request_state = request_convolution_size
        else
          call self%set_error('unknown command')
        end if
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

  subroutine set_read_bytes(self, size)
    class(connection), intent(inout) :: self
    integer, intent(in) :: size

    self%processed = 0
    self%buffer = achar(0)
    self%needed_bytes = size
    self%bytes_limit = size
    self%needed_fields = -1
    self%connection_state = connection_read
  end subroutine set_read_bytes

  subroutine set_read_fields(self, min_size, max_size, fields_count)
    class(connection), intent(inout) :: self
    integer, intent(in) :: min_size
    integer, intent(in) :: max_size
    integer, intent(in) :: fields_count

    self%processed = 0
    self%buffer = achar(0)
    self%needed_bytes = min_size
    self%bytes_limit = max_size
    self%needed_fields = fields_count
    self%connection_state = connection_read
  end subroutine set_read_fields

  subroutine set_error(self, error)
    class(connection), intent(inout) :: self
    character(len=*) :: error

    call skip(self%socket, self%buffer)

    self%processed = 0
    self%needed_bytes = len(error) + 1
    self%buffer(1:len(error)) = to_array(error)
    self%buffer(len(error) + 1) = delimiter
    self%connection_state = connection_write
  end subroutine set_error

  subroutine add_to_response(self, a)
    class(connection), intent(inout) :: self
    character, dimension(:), intent(in) :: a

    integer :: pos

    pos = self%needed_bytes
    self%buffer(pos+1 : pos+size(a)) = a
    self%needed_bytes = pos + size(a)
  end subroutine add_to_response

  subroutine add_to_response_str(self, s)
    class(connection), intent(inout) :: self
    character(len=*), intent(in) :: s
    call self%add_to_response(to_array(s))
    call self%add_to_response((/ Delimiter /))
  end subroutine add_to_response_str

  subroutine add_to_response_int(self, n)
    class(connection), intent(inout) :: self
    integer, intent(in) :: n
    call self%add_to_response(to_array(n))
    call self%add_to_response((/ Delimiter /))
  end subroutine add_to_response_int

  subroutine init_upload(self)
    class(connection), intent(inout) :: self
    integer :: n
    integer :: m
    integer :: desc
    integer :: key

    integer, dimension(1:1) :: offset
    integer :: npos
    integer :: mpos
    integer :: ndpos
    integer :: nkpos

    offset = findloc(self%buffer(1:self%processed), delimiter)
    npos = offset(1)
    if (npos.le.1.or.npos.gt.3) then
      call self%set_error('field n has bad size')
      return
    end if

    offset = findloc(self%buffer(npos+1:self%processed), delimiter)
    mpos = offset(1) + npos
    if ((mpos-npos).le.1.or.(mpos-npos).gt.3) then
      call self%set_error('field m has bad size')
      return
    end if

    offset = findloc(self%buffer(mpos+1:self%processed), delimiter)
    ndpos = offset(1) + mpos
    if ((ndpos-mpos).le.1.or.(ndpos-mpos).gt.3) then
      call self%set_error('field <length of desc> has bad size')
      return
    end if

    offset = findloc(self%buffer(ndpos+1:self%processed), delimiter)
    nkpos = offset(1) + ndpos
    if ((nkpos-ndpos).le.1.or.(nkpos-ndpos).gt.3) then
      call self%set_error('field <length of key> has bad size')
      return
    end if

    n = parse_int(self%buffer(1:npos-1))
    m = parse_int(self%buffer(npos+1:mpos-1))
    desc = parse_int(self%buffer(mpos+1:ndpos-1))
    key = parse_int(self%buffer(ndpos+1:nkpos-1))

    if (n.le.0.or.m.le.0.or.desc.le.0.or.key.le.0) then
      call self%set_error('one of fields too small')
      return
    end if

    if (n.gt.matrix_size.or.m.gt.matrix_size) then
      call self%set_error('image is too large')
      return
    end if

    if (desc.gt.text_size) then
      call self%set_error('desc is too long')
      return
    end if

    if (key.gt.text_size) then
      call self%set_error('key is too long')
      return
    end if

    self%extra%n = n
    self%extra%m = m
    self%extra%desc = desc
    self%extra%key = key
    call self%set_read_bytes(n * m + desc + key)
    self%request_state = request_upload
  end subroutine init_upload

  subroutine handle_upload(self)
    class(connection), intent(inout) :: self

    integer :: n
    integer :: m
    integer :: ndesc
    integer :: nkey
    character, dimension(1:id_size) :: id
    character, dimension(1:sha256_size) :: key_hash
    integer(1), dimension(:,:), allocatable :: matrix
    character, dimension(:), allocatable :: desc
    character, dimension(:), allocatable :: key

    n = self%extra%n
    m = self%extra%m
    ndesc = self%extra%desc
    nkey = self%extra%key

    matrix = reshape(to_int(self%buffer(1:n*m)), (/n, m/))
    desc = self%buffer(n*m+1:n*m+ndesc)
    key = self%buffer(n*m+ndesc+1:n*m+ndesc+nkey)

    key_hash = sha256_calc(key)

    id = db_store(self%buffer, matrix, desc, key_hash)

    if (id(1).eq.achar(0)) then
      call self%set_error('problem with image uploading')
    else
      self%processed = 0
      self%needed_bytes = 0
      self%connection_state = connection_write

      call self%add_to_response_str(ok)
      call self%add_to_response(id)
    end if
  end subroutine handle_upload

  subroutine init_download(self)
    class(connection), intent(inout) :: self
    integer :: key

    integer, dimension(1:1) :: offset
    integer :: kpos
    
    offset = findloc(self%buffer(1:self%processed), delimiter)
    kpos = offset(1)
    if (kpos.le.1.or.kpos.gt.3) then
      call self%set_error('field <length of key> has bad size')
      return
    end if
    key = parse_int(self%buffer(1:kpos-1))

    if (key.le.0.or.key.gt.text_size) then
      call self%set_error('key length has bad size')
      return
    end if

    self%extra%key = key

    call self%set_read_bytes(key + id_size)
    self%request_state = request_download
  end subroutine init_download

  subroutine handle_download(self)
    class(connection), intent(inout) :: self

    integer :: lkey
    integer(1), dimension(:,:), pointer :: matrix
    character, dimension(:), pointer :: desc
    character, dimension(:), pointer :: stored_key_hash
    character, dimension(1:sha256_size) :: key_hash
    character, dimension(:), allocatable :: id
    logical :: success
    integer :: msize
    integer, dimension(1:2) :: mshape

    lkey = self%extra%key
    id = self%buffer(1:id_size)
    key_hash = sha256_calc(self%buffer(id_size+1:id_size+lkey))

    success = db_load(self%buffer, id, matrix, desc, stored_key_hash)
    if (.not.success) then
      call self%set_error('image is not found')
      return
    end if
    if (size(stored_key_hash).ne.sha256_size.or.any(key_hash.ne.stored_key_hash)) then
      call self%set_error('image is not found')
      return
    end if

    msize = size(matrix)
    mshape = shape(matrix)

    self%processed = 0
    self%needed_bytes = 0
    self%connection_state = connection_write

    call self%add_to_response_str(ok)
    call self%add_to_response_int(mshape(1))
    call self%add_to_response_int(mshape(2))
    call self%add_to_response_int(size(desc))
    call self%add_to_response(transfer(matrix, self%buffer(1), msize))
    call self%add_to_response(desc)
  end subroutine

  subroutine init_convolution(self)
    class(connection), intent(inout) :: self
    integer :: n
    integer :: m

    integer, dimension(1:1) :: offset
    integer :: npos
    integer :: mpos
    character(len=2) :: ns
    character(len=2) :: ms

    offset = findloc(self%buffer(1:self%processed), delimiter)
    npos = offset(1)
    if (npos.le.1.or.npos.gt.3) then
      call self%set_error('field n has bad size')
      return
    end if

    offset = findloc(self%buffer(npos+1:self%processed), delimiter)
    mpos = offset(1) + npos
    if ((mpos-npos).le.1.or.(mpos-npos).gt.3) then
      call self%set_error('field m has bad size')
      return
    end if

    ns = to_string(self%buffer(1:npos-1), npos-1)
    ms = to_string(self%buffer(npos+1:mpos-1), mpos-npos-1)
    if (ns.ne.ms) then
      call self%set_error('kernel is not square')
      return
    end if

    n = parse_int(self%buffer(1:npos-1))
    m = parse_int(self%buffer(npos+1:mpos-1))

    if (n.le.1) then
      call self%set_error('kernel is too small')
      return
    end if

    if (n.gt.convolution_size) then
      call self%set_error('kernel is too large')
      return
    end if

    self%extra%n = n
    self%extra%m = m
    call self%set_read_bytes(id_size + n * m)
    self%request_state = request_convolution
  end subroutine init_convolution

  subroutine handle_convolution(self)
    class(connection), intent(inout) :: self

    integer :: kn
    integer :: km

    integer(1), dimension(:,:), pointer :: matrix
    character, dimension(:), pointer :: desc
    character, dimension(:), pointer :: stored_key_hash
    integer, dimension(:,:), allocatable :: res

    logical :: success
    character, dimension(:), allocatable :: id
    integer(1), dimension(:,:), allocatable :: kernel
    integer, dimension(1:2) :: rsizes
    integer :: rsize
    integer, dimension(1:2) :: msize

    kn = self%extra%n
    km = self%extra%m

    id = self%buffer(1:id_size)

    kernel = reshape(to_int(self%buffer(id_size + 1: id_size + kn * km)), (/kn, km/))

    if (count(kernel.ne.0).le.1) then
      call self%set_error('kernel is too simple')
      return
    end if

    success = db_load(self%buffer, id, matrix, desc, stored_key_hash)
    if (.not.success) then
      call self%set_error('image is not found')
      return
    end if

    msize = shape(matrix)

    if (kn.gt.msize(1).or.km.gt.msize(2)) then
      call self%set_error('kernel is larger than image')
      return
    end if

    res = convolution(matrix, kernel)
    rsizes = shape(res)
    rsize = 4 * size(res)

    self%processed = 0
    self%needed_bytes = 0
    self%connection_state = connection_write

    call self%add_to_response_str(ok)
    call self%add_to_response_int(rsizes(1))
    call self%add_to_response_int(rsizes(2))
    call self%add_to_response(transfer(res, self%buffer(1), rsize))
  end subroutine handle_convolution

  subroutine skip(socket, buffer)
    integer :: socket
    character(kind=c_char), dimension(:), intent(in) :: buffer
    integer :: readed

    do
      readed = tcp_read(socket, buffer)
      if (readed.le.0) then
        return
      end if
    end do
  end subroutine

end module connection_handler
