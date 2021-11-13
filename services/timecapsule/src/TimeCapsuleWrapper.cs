using System;
using System.Buffers;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using K4os.Compression.LZ4;

namespace timecapsule
{
	public static class TimeCapsuleWrapper
	{
		public static async Task<string> WrapAsync(Container item, CancellationToken token, Guid? key = null)
		{
			byte[] buffer1 = null, buffer2 = null;
			try
			{
				buffer1 = ArrayPool<byte>.Shared.Rent(ContainerMaxSize);
				buffer2 = ArrayPool<byte>.Shared.Rent(ContainerMaxSize);

				var encKey = key ?? (await Settings.ReadAsync(buffer1, token)).Key;

				var length = Write(new Span<byte>(buffer1), item.Id);
				length += Write(new Span<byte>(buffer1).Slice(length), item.CreateDate);
				length += Write(new Span<byte>(buffer1).Slice(length), item.ExpireDate);
				length += Write(new Span<byte>(buffer1).Slice(length), item.Text);
				length += Write(new Span<byte>(buffer1).Slice(length), item.Author);

				length = LZ4Codec.Encode(new ReadOnlySpan<byte>(buffer1, 0, length), buffer2);
				length = Encrypt(encKey, new ReadOnlySpan<byte>(buffer2, 0, length), buffer1);
				return Convert.ToBase64String(buffer1, 0, length);
			}
			finally
			{
				if(buffer1 != null) ArrayPool<byte>.Shared.Return(buffer1);
				if(buffer2 != null) ArrayPool<byte>.Shared.Return(buffer2);
			}
		}

		public static async Task<Container> UnwrapAsync(string value, CancellationToken token, Guid? key = null)
		{
			byte[] buffer1 = null, buffer2 = null;
			try
			{
				buffer1 = ArrayPool<byte>.Shared.Rent(ContainerMaxSize);
				buffer2 = ArrayPool<byte>.Shared.Rent(ContainerMaxSize);

				var decKey = key ?? (await Settings.ReadAsync(buffer1, token)).Key;

				Convert.TryFromBase64String(value, buffer1, out var length);
				length = Decrypt(decKey, new ReadOnlySpan<byte>(buffer1, 0, length), buffer2);
				length = LZ4Codec.Decode(new ReadOnlySpan<byte>(buffer2, 0, length), buffer1);

				length = 0;
				var id = ReadGuid(new ReadOnlySpan<byte>(buffer1), ref length);
				var createDate = ReadDateTime(new ReadOnlySpan<byte>(buffer1), ref length);
				var expireDate = ReadDateTime(new ReadOnlySpan<byte>(buffer1), ref length);
				var text = ReadString(new ReadOnlySpan<byte>(buffer1), ref length);
				var author = ReadString(new ReadOnlySpan<byte>(buffer1), ref length);

				return new Container { Id = id, CreateDate = createDate, ExpireDate = expireDate, Text = text, Author = author };
			}
			finally
			{
				if(buffer1 != null) ArrayPool<byte>.Shared.Return(buffer1);
				if(buffer2 != null) ArrayPool<byte>.Shared.Return(buffer2);
			}
		}

		private static int Encrypt(Guid key, ReadOnlySpan<byte> input, Span<byte> output)
		{
			var tag = output.Slice(0, AesGcm.TagByteSizes.MaxSize);
			var nonce = output.Slice(AesGcm.TagByteSizes.MaxSize, AesGcm.NonceByteSizes.MaxSize);
			var cipher = output.Slice(AesGcm.TagByteSizes.MaxSize + AesGcm.NonceByteSizes.MaxSize, input.Length);

			RandomNumberGenerator.Fill(nonce);

			Span<byte> k = stackalloc byte[16];
			key.TryWriteBytes(k);

			using var aes = new AesGcm(k);
			aes.Encrypt(nonce, input, cipher, tag);

			return tag.Length + nonce.Length + input.Length;
		}

		private static int Decrypt(Guid key, ReadOnlySpan<byte> input, Span<byte> output)
		{
			var tag = input.Slice(0, AesGcm.TagByteSizes.MaxSize);
			var nonce = input.Slice(AesGcm.TagByteSizes.MaxSize, AesGcm.NonceByteSizes.MaxSize);
			var cipher = input.Slice(AesGcm.TagByteSizes.MaxSize + AesGcm.NonceByteSizes.MaxSize);

			Span<byte> k = stackalloc byte[16];
			key.TryWriteBytes(k);

			using var aes = new AesGcm(k);
			aes.Decrypt(nonce, cipher, tag, output.Slice(0, cipher.Length));

			return input.Length - tag.Length - nonce.Length;
		}

		private static int Write(Span<byte> span, int val)
		{
			BitConverter.TryWriteBytes(span, val);
			return sizeof(int);
		}

		private static int Write(Span<byte> span, DateTime val)
		{
			var ticks = val.Ticks / 10000000L;
			span[0] = (byte)(ticks & 0xff);
			return 1 + Write(span.Slice(1), (int)(ticks >> 8));
		}

		private static int Write(Span<byte> span, Guid? val)
		{
			(val ?? Guid.Empty).TryWriteBytes(span);
			return GuidLength;
		}

		private static int Write(Span<byte> span, string value)
		{
			var len = Encoding.UTF8.GetByteCount(value ??= string.Empty);
			if(len > 255) throw new ArgumentException("Value too long", nameof(value));
			span[0] = (byte)Encoding.UTF8.GetBytes(value.ToLower(), span.Slice(1, len));
			return 1 + len;
		}

		private static int ReadInt32(ReadOnlySpan<byte> span, ref int offset)
		{
			var value = BitConverter.ToInt32(span.Slice(offset, sizeof(int)));
			offset += sizeof(int);
			return value;
		}

		private static DateTime ReadDateTime(ReadOnlySpan<byte> span, ref int offset)
			=> new((span[offset++] + ((long)ReadInt32(span, ref offset) << 8)) * 10000000L);

		private static Guid? ReadGuid(ReadOnlySpan<byte> span, ref int offset)
		{
			var value = new Guid(span.Slice(offset, GuidLength));
			offset += GuidLength;
			return value == Guid.Empty ? null : value;
		}

		private static string ReadString(ReadOnlySpan<byte> span, ref int offset)
		{
			var length = span[offset];
			var value = Encoding.UTF8.GetString(span.Slice(offset + 1, length));
			offset += 1 + length;
			return value == string.Empty ? null : value;
		}

		private const int GuidLength = 16;
		private const int ContainerMaxSize = 4096;
	}
}
