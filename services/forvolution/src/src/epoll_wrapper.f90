module epoll_wrapper
  use iso_c_binding, only: c_int, c_ptr, c_loc

  implicit none

  private
  public epoll, epoll_event

  type, bind(c) :: epoll_event
    integer(kind=c_int) :: socket
    integer(kind=c_int) :: mode
  end type epoll_event

  type :: epoll
    integer, private :: size = 0
    type(epoll_event), dimension(:), allocatable, private :: buffer
    integer, private :: epfd
  contains
    procedure, public :: init
    procedure, public :: add
    procedure, public :: try_update
    procedure, public :: update
    procedure, public :: wait
  end type epoll

  interface

    function c_epoll_create(cnt) result(epfd) bind(c, name='c_epoll_create')
      import c_int
      integer(kind=c_int), intent(in), value :: cnt
      integer(kind=c_int) :: epfd
    end function c_epoll_create

    function c_epoll_add(epfd, socket, mode) result(r) bind(c, name='c_epoll_add')
      import c_int
      integer(kind=c_int), intent(in), value :: epfd, socket, mode
      integer(kind=c_int) :: r
    end function c_epoll_add

    function c_epoll_update(epfd, socket, mode) result(r) bind(c, name='c_epoll_update')
      import c_int
      integer(kind=c_int), intent(in), value :: epfd, socket, mode
      integer(kind=c_int) :: r
    end function c_epoll_update

    function c_epoll_wait(epfd, buffer) result(cnt) bind(c, name='c_epoll_wait')
      import c_int, c_ptr
      integer(kind=c_int), intent(in), value :: epfd
      type(c_ptr), intent(in), value :: buffer
      integer(kind=c_int) :: cnt
    end function c_epoll_wait
  end interface

contains

  function init(self, cnt) result(epfd)
    class(epoll), intent(inout) :: self
    integer, intent(in) :: cnt
    integer :: epfd
    self%size = cnt
    allocate(self%buffer(cnt))
    self%epfd = c_epoll_create(cnt)
    epfd = self%epfd
  end function init

  function add(self, socket, mode) result(r)
    class(epoll), intent(inout) :: self
    integer, intent(in) :: socket, mode
    integer :: r
    r = c_epoll_add(self%epfd, socket, mode)
  end function add

  function try_update(self, socket, mode) result(r)
    class(epoll), intent(inout) :: self
    integer, intent(in) :: socket, mode
    integer :: r
    r = c_epoll_update(self%epfd, socket, mode)
  end function try_update

  subroutine update(self, socket, mode)
    class(epoll), intent(inout) :: self
    integer, intent(in) :: socket, mode
    integer :: dummy
    dummy = c_epoll_update(self%epfd, socket, mode)
  end subroutine update

  function wait(self) result(events)
    class(epoll), intent(inout), target :: self
    type(epoll_event), dimension(:), allocatable :: events
    integer :: r
    
    r = c_epoll_wait(self%epfd, c_loc(self%buffer))
    if (r < 0) then
      if (allocated(events)) then
        deallocate(events)
      end if
    else
      events = self%buffer(:r)
    end if
  end function wait

end module epoll_wrapper
