using System;
using System.Net;

namespace checker.net
{
	internal static class HttpStatusToExitCode
	{
		public static ExitCode ToExitCode(this HttpStatusCode status)
		{
			if((int)status == 200)
				return ExitCode.OK;
			if((int)status >= 500 || (int)status == 499 || status == 0)
				return ExitCode.DOWN;
			return ExitCode.MUMBLE;
		}

		public static string ToReadableCode(this HttpStatusCode status)
			=> status == 0 ? "connection failed" : (int)status == 499 ? "timed out" : $"{(int)status} {(Enum.IsDefined(status) ? status.ToString("G") : "Unknown")}";
	}
}
