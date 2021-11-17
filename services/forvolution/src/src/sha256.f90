module sha256
  implicit none

  private 
  public sha256_calc, sha256_size

  integer, parameter :: sha256_size = 32
  integer, parameter :: block_size = 64
  integer, parameter :: rounds_count = 64
  integer, parameter :: state_size = 8
  integer(8), dimension(1:rounds_count), parameter :: k = (/ &
    1116352408_8, 1899447441_8, 3049323471_8, 3921009573_8,  961987163_8, 1508970993_8, 2453635748_8, 2870763221_8, &
    3624381080_8,  310598401_8,  607225278_8, 1426881987_8, 1925078388_8, 2162078206_8, 2614888103_8, 3248222580_8, &
    3835390401_8, 4022224774_8,  264347078_8,  604807628_8,  770255983_8, 1249150122_8, 1555081692_8, 1996064986_8, &
    2554220882_8, 2821834349_8, 2952996808_8, 3210313671_8, 3336571891_8, 3584528711_8,  113926993_8,  338241895_8, &
     666307205_8,  773529912_8, 1294757372_8, 1396182291_8, 1695183700_8, 1986661051_8, 2177026350_8, 2456956037_8, &
    2730485921_8, 2820302411_8, 3259730800_8, 3345764771_8, 3516065817_8, 3600352804_8, 4094571909_8,  275423344_8, &
     430227734_8,  506948616_8,  659060556_8,  883997877_8,  958139571_8, 1322822218_8, 1537002063_8, 1747873779_8, &
    1955562222_8, 2024104815_8, 2227730452_8, 2361852424_8, 2428436474_8, 2756734187_8, 3204031479_8, 3329325298_8 /)

contains
  function sha256_calc(ch) result(r)
    character, dimension(:), intent(in) :: ch
    character, dimension(1:sha256_size) :: r

    integer :: processed
    integer :: last_chunk_data_size
    integer :: i
    integer(8), dimension(1:state_size) :: state
    character, dimension(1:block_size) :: last_chunk

    state = (/1779033703_8, 3144134277_8, 1013904242_8, 2773480762_8, 1359893119_8, 2600822924_8, 528734635_8, 1541459225_8/)

    processed = 0
    do while ((processed + block_size).le.size(ch))
      state = state + consume_chunk(ch(processed + 1 : processed + block_size), state)
      processed = processed + block_size
    end do

    last_chunk_data_size = size(ch) - processed
    if (size(ch).gt.0) then
      last_chunk(:last_chunk_data_size) = ch(processed+1:)
    end if
    last_chunk(last_chunk_data_size + 1) = char(128)
    if ((last_chunk_data_size + 1 + 8).gt.block_size) then
      last_chunk(last_chunk_data_size + 2 :) = char(0)
      state = state + consume_chunk(last_chunk, state)
      last_chunk(:size(last_chunk) - 8) = char(0)
    else
      last_chunk(last_chunk_data_size+2 : size(last_chunk) - 8) = char(0)
    end if

    last_chunk(size(last_chunk) - 7:) = convert8(int(size(ch), 8) * 8)

    state = state + consume_chunk(last_chunk, state)

    do i = 1, state_size
      r(i * 4 - 3 : i * 4) = convert4(state(i))
    end do

  end function sha256_calc

  function consume_chunk(d, state) result(r)
    character, dimension(1:block_size), intent(in) :: d
    integer(8), dimension(1:8), intent(in) :: state
    integer(8), dimension(1:8) :: r

    integer :: i
    integer(8) :: tmp1
    integer(8) :: tmp2
    integer(8), dimension(rounds_count) :: w

    w = expand(d)

    r = state
    do i = 1, rounds_count
      tmp1 = r(8) + sigma1(r(5)) + ch(r(5), r(6), r(7)) + k(i) + w(i)
      tmp2 = sigma0(r(1)) + ma(r(1), r(2), r(3))

      r(2:8) = r(1:7)
      r(1) = iand(tmp1 + tmp2, z'ffffffff')
      r(5) = iand(r(5) + tmp1, z'ffffffff')
    end do
  end function consume_chunk

  function expand(ch) result(w)
    character, dimension(1:block_size), intent(in) :: ch
    integer(8), dimension(1:rounds_count) :: w
  
    integer :: i
    character, dimension(1:8) :: buffer
  
    buffer = char(0)
    do i = 1, 16
      buffer(1:4) = ch(i * 4 : i * 4 - 3 : -1)
      w(i) = transfer(buffer, w(i))
    end do
  
    do i = 17, 64
      w(i) = isum((/w(i - 16), s0(w(i - 15)), w(i - 7), s1(w(i - 2))/))
    end do
  end function expand

  function ch(e, f, g) result(r)
    integer(8), intent(in) :: e
    integer(8), intent(in) :: f
    integer(8), intent(in) :: g
    integer(8) :: r

    r = ieor(iand(e, f), iand(not(e), g))
  end function ch

  function ma(a, b, c) result(r)
    integer(8), intent(in) :: a
    integer(8), intent(in) :: b
    integer(8), intent(in) :: c
    integer(8) :: r

    r = ieors((/iand(a, b), iand(b, c), iand(c, a)/))
  end function ma

  function sigma0(a) result(r)
    integer(8), intent(in) :: a
    integer(8) :: r

    r = ieors(irr(a, (/2, 13, 22/)))
  end function sigma0

  function sigma1(e) result(r)
    integer(8), intent(in) :: e
    integer(8) :: r

    r = ieors(irr(e, (/6, 11, 25/)))
  end function sigma1

  function s0(x) result(r)
    integer(8), intent(in) :: x
    integer(8) :: r

    r = ieors((/irr(x, 7), irr(x, 18), irs(x, 3)/))
  end function s0

  function s1(x) result(r)
    integer(8), intent(in) :: x
    integer(8) :: r

    r = ieors((/irr(x, 17), irr(x, 19), irs(x, 10)/))
  end function s1
 
  function isum(a) result(r)
    integer(8), dimension(:), intent(in) :: a
    integer(8) :: r

    integer :: i

    r = 0
    do i = 1, size(a)
      r = r + a(i)
    end do
    r = iand(r, z'ffffffff')
  end function isum

  function ieors(a) result(r)
    integer(8), dimension(:), intent(in) :: a
    integer(8) :: r

    integer :: i

    r = 0
    do i = 1, size(a)
      r = ieor(r, a(i))
    end do
  end function ieors

  elemental function irr(x, sh) result(r)
    integer(8), intent(in) :: x
    integer, intent(in) :: sh
    integer(8) :: r

    r = ishftc(x, -sh, 32)
  end function irr

  elemental function irs(x, sh) result(r)
    integer(8), intent(in) :: x
    integer, intent(in) :: sh
    integer(8) :: r

    r = ishft(x, -sh)
  end function irs

  function convert8(x) result(r)
    integer(8), intent(in) :: x
    character, dimension(1:8) :: r

    r(8:1:-1) = transfer(x, r)
  end function convert8

  function convert4(x) result(r)
    integer(8), intent(in) :: x
    character, dimension(1:4) :: r

    character, dimension(1:8) :: buffer

    buffer = transfer(x, buffer)
    r = buffer(4:1:-1)
  end function convert4
end module sha256
