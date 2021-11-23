using System;

namespace OAuthServer.Configuration
{
    public class ApplicationConfiguration
    {
        public string ClientId { get; set; }

        public TimeSpan TokenIssueFrequency { get; set; }

        public string RedirectUriRegex { get; set; }
    }
}