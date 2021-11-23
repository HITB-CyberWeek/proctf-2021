using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.Configuration;
using OAuthServer.Configuration;

namespace OAuthServer
{
    public class TokenManager : ITokenManager
    {
        private readonly Dictionary<string, TokenType> tokens;

        public TokenManager(IConfiguration configuration)
        {
            tokens = configuration.GetSection("Tokens").Get<TokenConfiguration[]>().ToDictionary(c => c.Token, c => c.Type);
        }

        public TokenType GetTokenType(string token)
        {
            return tokens.TryGetValue(token, out var type) ? type : TokenType.Unknown;
        }
    }
}