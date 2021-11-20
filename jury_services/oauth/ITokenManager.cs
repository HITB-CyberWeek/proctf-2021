namespace OAuthServer
{
    public interface ITokenManager
    {
        TokenType GetTokenType(string token);
    }
}