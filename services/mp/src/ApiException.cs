using System;
using System.Globalization;
using static System.String;

namespace mp
{
    public class ApiException : Exception
    {
        public ApiException()  { }

        public ApiException(string message) : base(message) { }

        public ApiException(string message, params object[] args)
            : base(Format(CultureInfo.CurrentCulture, message, args))
        {
        }
    }
}
