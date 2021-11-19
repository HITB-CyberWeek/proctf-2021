using System;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using mp.Entities;

namespace mp.Services
{
    public class UserService
    {
        private readonly UsersStorage usersStorage;

        public UserService(UsersStorage usersStorage)
        {
            this.usersStorage = usersStorage;
        }

        //TODO trim login
        public User ValidateCredentials(string login, string password)
        {
            var user = usersStorage.Find(login);
            if(user == null)
                return null;
            if(!ValidatePasswordHash(password, user.PasswordHash))
                return null;
            return user;
        }

        public async Task<User> Create(string login, string password)
        {
            if(string.IsNullOrWhiteSpace(login) || string.IsNullOrWhiteSpace(password))
                throw new ApiException("Non-empty Login and Password required");

            var user = new User {Login = login, PasswordHash = CreatePasswordHash(password)};
            if(!await usersStorage.TryAdd(user))
                throw new ApiException($"Login '{user.Login}' is already used");

            return user;
        }

        public User Get(string login)
        {
            var user = Find(login);
            if(user == null)
                throw new ApiException($"User {login} not found");
            return user;
        }

        public User Find(string login)
        {
            return usersStorage.Find(login);
        }

        private static byte[] CreatePasswordHash(string password)
        {
            if(password == null || string.IsNullOrWhiteSpace(password))
                throw new ArgumentNullException(nameof(password));

            using var sha256 = new SHA256Managed();
            return sha256.ComputeHash(Encoding.UTF8.GetBytes(password));
        }

        private static bool ValidatePasswordHash(string password, byte[] storedHash)
        {
            if(string.IsNullOrEmpty(password))
                throw new ArgumentException(nameof(password));

            using var sha256 = new SHA256Managed();
            if(storedHash.Length * 8 != sha256.HashSize)
                throw new ArgumentException(nameof(storedHash));

            var isOk = true;
            var computedHash = sha256.ComputeHash(Encoding.UTF8.GetBytes(password));
            for(int i = 0; i < computedHash.Length; i++)
            {
                if(computedHash[i] != storedHash[i])
                    isOk = false;
            }
            return isOk;
        }
    }
}