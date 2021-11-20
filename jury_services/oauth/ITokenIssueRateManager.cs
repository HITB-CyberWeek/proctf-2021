using System;

namespace OAuthServer
{
    public interface ITokenIssueRateManager
    {
        bool TryIssueToken(string application, string instanceId, string groupId, out RejectionReason rejectionReason,
            out TimeSpan timeToWait);
    }
}