using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.Configuration;
using OAuthServer.Configuration;

namespace OAuthServer
{
    public class TokenIssueRateManager : ITokenIssueRateManager
    {
        private readonly ITokenManager tokenManager;
        private readonly Dictionary<string, TimeSpan> frequencies;

        private readonly ConcurrentDictionary<string, DateTime> tokenIssueDates =
            new ConcurrentDictionary<string, DateTime>();

        public TokenIssueRateManager(IConfiguration configuration, ITokenManager tokenManager)
        {
            this.tokenManager = tokenManager;
            frequencies = configuration.GetSection("Applications").Get<ApplicationConfiguration[]>()
                .ToDictionary(c => c.ClientId, c => c.TokenIssueFrequency);
        }

        public bool TryIssueToken(string application, string instanceId, string groupId, out RejectionReason rejectionReason, out TimeSpan timeToWait)
        {
            if (!frequencies.TryGetValue(application, out var frequency))
            {
                rejectionReason = RejectionReason.NotFound;
                timeToWait = default;
                return false;
            }

            if (tokenManager.GetTokenType(groupId) == TokenType.Checksystem)
            {
                rejectionReason = default;
                timeToWait = default;
                return true;
            }

            var key = GetKey(application, instanceId, groupId);
            var now = DateTime.UtcNow;

            if (tokenIssueDates.TryGetValue(key, out var lastIssueDate))
            {
                if (now.Subtract(lastIssueDate) < frequency)
                {
                    rejectionReason = RejectionReason.ShouldWait;
                    timeToWait = lastIssueDate + frequency - now;
                    return false;
                }

                if (tokenIssueDates.TryUpdate(key, now, lastIssueDate))
                {
                    rejectionReason = default;
                    timeToWait = default;
                    return true;
                }

                return TryIssueToken(application, instanceId, groupId, out rejectionReason, out timeToWait);
            }

            if (tokenIssueDates.TryAdd(key, now))
            {
                rejectionReason = default;
                timeToWait = default;
                return true;
            }

            return TryIssueToken(application, instanceId, groupId, out rejectionReason, out timeToWait);
        }

        private static string GetKey(string application, string instanceId, string groupId)
        {
            return application + instanceId + groupId;
        }
    }
}