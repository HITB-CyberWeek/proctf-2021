using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using mp.Entities;

namespace mp.Services
{
    public interface IUserService
    {
        User ValidateCredentials(string login, string password);
        User Create(User user, string password);
        User Find(string login);
        User Get(string login);
    }

    class UsersStorage
    {
        private ConcurrentDictionary<string, User> users = new();

        public bool TryCreate(User user)
        {
            return users.TryAdd(user.Login, user);
        }

        public User Find(string login)
        {
            return login != null && users.TryGetValue(login, out var result) ? result : null;
        }
    }

    public class UserService : IUserService
    {
        private string baseDir;
        private readonly UsersStorage usersStorage;

        public UserService(string baseDir)
        {
            this.baseDir = baseDir;
            this.usersStorage = new UsersStorage();
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

        public User Create(User user, string password)
        {
            if (string.IsNullOrEmpty(password))
                throw new ApiException("Password required");

            CreatePasswordHash(password, out var passwordHash);

            user.PasswordHash = passwordHash;

            if(!usersStorage.TryCreate(user))
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

        private static void CreatePasswordHash(string password, out byte[] passwordHash)
        {
            if(password == null || string.IsNullOrWhiteSpace(password))
                throw new ArgumentNullException(nameof(password));

            using var sha512 = new SHA512Managed();
            passwordHash = sha512.ComputeHash(Encoding.UTF8.GetBytes(password));
        }

        private static bool ValidatePasswordHash(string password, byte[] storedHash)
        {
            if(password == null) throw new ArgumentNullException(nameof(password));
            if(string.IsNullOrWhiteSpace(password))
                throw new ArgumentException(nameof(password));
            
            if(storedHash.Length != 64)
                throw new ArgumentException(nameof(storedHash));

            bool isOk = true;
            using var hmac = new SHA512Managed();
            var computedHash = hmac.ComputeHash(Encoding.UTF8.GetBytes(password));
            for(int i = 0; i < computedHash.Length; i++)
            {
                if(computedHash[i] != storedHash[i])
                    isOk = false;
            }
            return isOk;
        }
    }
}