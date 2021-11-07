using System;
using System.Buffers;
using System.Security.Cryptography;
using System.Text;
using K4os.Compression.LZ4;

namespace checker.timecapsule
{
	public static class TimeCapsuleWrapper
	{
		public static Container Unwrap(string value, Guid key)
		{
			byte[] buffer1 = null, buffer2 = null;
			try
			{
				buffer1 = ArrayPool<byte>.Shared.Rent(ContainerMaxSize);
				buffer2 = ArrayPool<byte>.Shared.Rent(ContainerMaxSize);

				Convert.TryFromBase64String(value, buffer1, out var length);
				length = Decrypt(key, new ReadOnlySpan<byte>(buffer1, 0, length), buffer2);
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

		private static long ReadInt64(ReadOnlySpan<byte> span, ref int offset)
		{
			var value = BitConverter.ToInt64(span.Slice(offset, sizeof(long)));
			offset += sizeof(long);
			return value;
		}

		private static DateTime ReadDateTime(ReadOnlySpan<byte> span, ref int offset)
			=> new(ReadInt64(span, ref offset));

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
