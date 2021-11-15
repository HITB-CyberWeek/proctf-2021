namespace mp.Entities
{
    public class User
    {
        public string Login { get; set; }
        public byte[] PasswordHash { get; set; }
    }
}
